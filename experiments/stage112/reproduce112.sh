#!/usr/bin/env bash
# Host-only reproduction. No Android, original save, native game or production mutation.
# Usage: bash reproduce112.sh STAGE84.zip STAGE77.zip STAGE79.zip UPSTREAM_SaveRestartActivity.java
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python3 - "$1" "$2" "$3" "$work" <<'PY'
import hashlib,pathlib,sys,zipfile
pins=['02c4347b901f9004bfc1fdcc674e4ad5e6c0519a56ef82f84f2990f73998e8d8','de4e48482b1cb5f9355c0aa277f87f22a71a365e145aefcfb3479f95d12ec38d','715cde3c52e318ced3ff009397f41878ae946c8d8b9bc7ce37c316641145e928']
for path,pin,stage in zip(sys.argv[1:4],pins,[84,77,79]):
    assert hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()==pin
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(set(z.namelist()))
        z.extractall(pathlib.Path(sys.argv[4])/f'parent{stage}')
PY
python3 "$here/prepare_pre_native112.py" "$work/parent84/src/NativeStartupTrial.java" "$work/NativeStartupTrial.java"
mkdir -p "$work/classes" "$work/extra/android/os"
echo 'package android.os; public interface Parcelable {}' > "$work/extra/android/os/Parcelable.java"
javac -cp "$work/parent77/classes" -d "$work/classes" $(find "$work/parent77/mocksrc" -name '*.java' ! -path '*/android/content/pm/PackageManager.java') "$work/parent79/mockoverlay/android/util/Log.java" "$work/parent79/PackageManager.java" "$work/NativeStartupTrial.java" "$work/parent79/tests/PopulatedProfileTest.java" "$work/extra/android/os/Parcelable.java" "$here/PreNativeProfile112Test.java"
java --add-opens java.base/java.io=ALL-UNNAMED -cp "$work/classes:$work/parent77/classes" com.exvius.local.PreNativeProfile112Test
python3 "$here/prepare_restart112.py" "$4" "$work/SaveRestartActivity.java"
s="$work/restart-stubs"
mkdir -p "$s"/{android/app,android/content,android/os,android/system,android/util,com/exvius/local} "$work/restart-classes"
cat > "$s/android/app/Activity.java" <<'EOF'
package android.app; import android.content.Intent; import android.os.Bundle;
public class Activity { public static final String ACTIVITY_SERVICE="activity"; public final Intent intent=new Intent(); public final ActivityManager am=new ActivityManager(); public final java.util.Queue<Runnable> ui=new java.util.ArrayDeque<>(); public int launches, finishes; public boolean failLaunch; public void onCreate(Bundle b){} protected void onSaveInstanceState(Bundle b){} protected void onDestroy(){} public void onBackPressed(){} public Intent getIntent(){return intent;} public Object getSystemService(String s){return am;} public String getPackageName(){return "fixture";} public void runOnUiThread(Runnable r){ui.add(r);} public void startActivity(Intent i){if(failLaunch)throw new IllegalStateException("fixture");launches++;} public void finish(){finishes++;}}
EOF
cat > "$s/android/app/ActivityManager.java" <<'EOF'
package android.app; public class ActivityManager {public java.util.List<RunningAppProcessInfo> processes=new java.util.ArrayList<>();public java.util.List<RunningAppProcessInfo> getRunningAppProcesses(){return processes;}public static class RunningAppProcessInfo {public int pid,uid;public String processName;}}
EOF
cat > "$s/android/content/Intent.java" <<'EOF'
package android.content; public class Intent {public static final int FLAG_ACTIVITY_NEW_TASK=1,FLAG_ACTIVITY_CLEAR_TASK=2;public int pid=123,slot=1;public boolean delete,importing,create; public int getIntExtra(String k,int d){return k.equals("pid")?pid:k.equals("slot")?slot:d;}public boolean getBooleanExtra(String k,boolean d){return k.equals("delete")?delete:k.equals("import")?importing:k.equals("create")?create:d;}public Intent setClassName(String p,String c){return this;}public Intent addFlags(int f){return this;}}
EOF
cat > "$s/android/os/Bundle.java" <<'EOF'
package android.os; public class Bundle { public boolean getBoolean(String k){return true;} public void putBoolean(String k,boolean v){} }
EOF
cat > "$s/android/os/Handler.java" <<'EOF'
package android.os; public class Handler {public static int posts; public boolean postDelayed(Runnable r,long delay){posts++;return true;}public void removeCallbacksAndMessages(Object o){}}
EOF
cat > "$s/android/os/Process.java" <<'EOF'
package android.os; public class Process {public static int kills; public static int myPid(){return 321;}public static int myUid(){return 1000;}public static void killProcess(int pid){kills++;}}
EOF
cat > "$s/android/system/ErrnoException.java" <<'EOF'
package android.system; public class ErrnoException extends Exception {public final int errno; public ErrnoException(int n){errno=n;}}
EOF
cat > "$s/android/system/OsConstants.java" <<'EOF'
package android.system; public class OsConstants {public static final int ESRCH=3;}
EOF
cat > "$s/android/system/Os.java" <<'EOF'
package android.system; public class Os {public static int errno=3;public static void kill(int p,int signal)throws ErrnoException{if(errno!=0)throw new ErrnoException(errno);}}
EOF
cat > "$s/android/util/Log.java" <<'EOF'
package android.util; public class Log {public static int e(String tag,String msg){return 0;}}
EOF
cat > "$s/com/exvius/local/BootstrapAdmissionGate.java" <<'EOF'
package com.exvius.local; final class BootstrapAdmissionGate {static boolean allow;static void requireGameplayAdmission(){if(!allow)throw new IllegalStateException("held");}}
EOF
cat > "$s/com/exvius/local/SaveSlots.java" <<'EOF'
package com.exvius.local; final class SaveSlots {static int calls;static boolean fail;static void select(SaveRestartActivity a,int s,boolean c)throws java.io.IOException{calls++;if(fail)throw new java.io.IOException("fixture");}static void recoverDelete(SaveRestartActivity a)throws java.io.IOException{select(a,0,false);}}
EOF
cat > "$s/com/exvius/local/SaveTransferActivity.java" <<'EOF'
package com.exvius.local; final class SaveTransferActivity {static void install(SaveRestartActivity a)throws java.io.IOException{SaveSlots.select(a,0,false);}}
EOF
javac -d "$work/restart-classes" "$work/SaveRestartActivity.java" "$here/Restart112Test.java" $(find "$s" -name '*.java')
java -cp "$work/restart-classes" com.exvius.local.Restart112Test
