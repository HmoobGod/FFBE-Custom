#!/usr/bin/env bash
# Reproduce Stage110 adapter tests from the pinned original Java file.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python3 "$here/stage_cocos_drain110.py" "$1" "$work/LocalCocosTasks.java"
mkdir -p "$work/stubs/android/os" "$work/stubs/com/exvius/local"
cat > "$work/stubs/android/os/Looper.java" <<'EOF'
package android.os;
public class Looper { public static Looper getMainLooper(){return new Looper();} }
EOF
cat > "$work/stubs/android/os/Handler.java" <<'EOF'
package android.os;
import java.util.concurrent.LinkedBlockingQueue;
public class Handler {
    public static final LinkedBlockingQueue<Runnable> QUEUE=new LinkedBlockingQueue<>();
    public Handler(Looper looper){}
    public boolean post(Runnable r){return QUEUE.offer(r);}
}
EOF
cat > "$work/stubs/com/exvius/local/LocalGameBridge.java" <<'EOF'
package com.exvius.local;
import java.io.*;
import java.net.*;
final class LocalGameBridge {
    static HttpURLConnection openConnection(String address)throws IOException{
        return new HttpURLConnection(new URL(address)){
            public void disconnect(){} public boolean usingProxy(){return false;} public void connect(){}
            public int getResponseCode(){return 200;} public long getContentLengthLong(){return 3;}
            public InputStream getInputStream(){return new ByteArrayInputStream(new byte[]{1,2,3});}
        };
    }
    static boolean existingFile(String address,String dest){return false;}
}
EOF
cat > "$work/stubs/com/exvius/local/CocosAdapter110Test.java" <<'EOF'
package com.exvius.local;
import android.os.Handler;
import java.util.*;
import java.util.concurrent.TimeUnit;
final class CocosAdapter110Test {
    static void check(boolean value){if(!value)throw new AssertionError();}
    final Queue<Integer> _taskQueue=new ArrayDeque<>();
    int starts,progress,finishes,nexts;
    boolean chain=true;
    private void onStart(int id){starts++;}
    private void onProgress(int id,long delta,long total,long expected){check(total==3&&expected==3);progress++;}
    private void onFinish(int id,int status,String detail,byte[] bytes){check(status==0&&Arrays.equals(bytes,new byte[]{1,2,3}));finishes++;}
    private void runNextTaskIfExists(){nexts++;if(chain){chain=false;LocalCocosTasks.load(this,2,"http://offline.invalid/","");}}
    static void callback()throws Exception{Runnable task=Handler.QUEUE.poll(5,TimeUnit.SECONDS);check(task!=null);task.run();}
    static CocosTaskDrain110.Lease awaitLease(){long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(5);do{CocosTaskDrain110.Lease l=LocalCocosTasks.tryAcquireTaskDrain110();if(l!=null)return l;Thread.yield();}while(System.nanoTime()<end);throw new AssertionError("drain never became idle");}
    public static void main(String[] args)throws Exception{
        CocosAdapter110Test owner=new CocosAdapter110Test();
        LocalCocosTasks.load(owner,1,"http://offline.invalid/","");
        callback();callback();check(LocalCocosTasks.tryAcquireTaskDrain110()==null);
        callback();check(LocalCocosTasks.tryAcquireTaskDrain110()==null);
        callback();callback();callback();check(owner.starts==2&&owner.progress==2&&owner.finishes==2&&owner.nexts==2);
        System.out.println("PASS original start/progress/finish/next callback ordering and nested worker lifetime");
        try(CocosTaskDrain110.Lease l=awaitLease()){
            try{LocalCocosTasks.load(owner,3,"http://offline.invalid/","");throw new AssertionError();}catch(IllegalStateException expected){}
            owner._taskQueue.add(9);try{LocalCocosTasks.cancel(owner);throw new AssertionError();}catch(IllegalStateException expected){}check(owner._taskQueue.size()==1);
        }
        LocalCocosTasks.cancel(owner);check(owner._taskQueue.isEmpty());awaitLease().close();
        System.out.println("PASS scoped exclusion of new load/cancel and restoration after release");
    }
}
EOF
javac -d "$work/classes" "$here/CocosTaskDrain110.java" "$here/CocosTaskDrain110Test.java" "$work/LocalCocosTasks.java" "$work/stubs/android/os/"*.java "$work/stubs/com/exvius/local/"*.java
java -cp "$work/classes" com.exvius.local.CocosTaskDrain110Test
java -cp "$work/classes" com.exvius.local.CocosAdapter110Test
