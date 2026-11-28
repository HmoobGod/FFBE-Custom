package com.exvius.local;
import java.lang.reflect.*;
import android.os.Bundle;
final class Restart112Test {
    static int passed;
    static void ok(boolean b){if(!b)throw new AssertionError();}
    static void step(SaveRestartActivity a)throws Exception{Method m=SaveRestartActivity.class.getDeclaredMethod("handoff");m.setAccessible(true);try{m.invoke(a);}catch(InvocationTargetException e){throw (Exception)e.getCause();}}
    static SaveRestartActivity fresh(){SaveSlots.calls=0;SaveSlots.fail=false;android.os.Process.kills=0;android.system.Os.errno=3;BootstrapAdmissionGate.allow=true;return new SaveRestartActivity();}
    static void pass(String s){System.out.println("PASS "+s);passed++;}
    public static void main(String[] args)throws Exception {
        SaveRestartActivity a=fresh();BootstrapAdmissionGate.allow=false;try{a.onCreate(null);throw new AssertionError();}catch(IllegalStateException expected){}try{step(a);throw new AssertionError();}catch(IllegalStateException expected){}ok(SaveSlots.calls==0&&a.ui.isEmpty());pass("existing admission gate preserved");
        a=fresh();a.intent.pid=-1;step(a);ok(a.ui.isEmpty()&&SaveSlots.calls==0);a.intent.pid=123;step(a);ok(a.ui.isEmpty()&&SaveSlots.calls==0);pass("failed identity does not launch or retry");
        a=fresh();android.system.Os.errno=1;step(a);ok(a.ui.isEmpty()&&SaveSlots.calls==0);pass("unknown stopped-process status blocks handoff");
        a=fresh();android.system.Os.errno=0;step(a);ok(a.ui.isEmpty()&&SaveSlots.calls==0);pass("live PID does not perform handoff");
        a=fresh();SaveSlots.fail=true;step(a);ok(SaveSlots.calls==1&&a.ui.isEmpty());SaveSlots.fail=false;step(a);ok(SaveSlots.calls==1&&a.ui.isEmpty());pass("failed save action cannot launch or replay");
        a=fresh();a.onCreate(new Bundle());step(a);ok(SaveSlots.calls==0&&a.ui.isEmpty());pass("saved instance state cannot authorize handoff");
        a=fresh();step(a);ok(SaveSlots.calls==1&&a.ui.size()==1);step(a);ok(SaveSlots.calls==1&&a.ui.size()==1);a.ui.remove().run();ok(a.launches==1&&a.finishes==1);pass("successful fixture handoff launches exactly once");
        a=fresh();step(a);a.onDestroy();a.ui.remove().run();ok(a.launches==0&&a.finishes==0);pass("destroyed activity cannot launch queued native activity");
        System.out.println(passed+"/8 PASS — mock stopped-process handoff only");
    }
}
