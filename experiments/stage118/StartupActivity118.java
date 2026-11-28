package org.ffbe.diagnostic95;
import android.app.*;import android.os.*;import android.widget.*;import android.content.Context;
import java.util.concurrent.*;import java.util.concurrent.atomic.AtomicBoolean;
/** Private fixture review, based on Stage109 Activity lifecycle. Never launches FFBE. */
public final class StartupActivity118 extends Activity {
 private static final ExecutorService WORK=Executors.newSingleThreadExecutor();
 private static final AtomicBoolean ACTIVE=new AtomicBoolean();
 private static volatile String last="No probe has run.";private static volatile boolean blocked;
 private static volatile Session117 retained;
 private TextView status;private AlertDialog dialog;private AtomicBoolean pending;private boolean stopped;private int generation;
 @Override public void onCreate(Bundle state){super.onCreate(state);LinearLayout v=new LinearLayout(this);v.setOrientation(LinearLayout.VERTICAL);v.setPadding(24,24,24,24);status=new TextView(this);status.setText(last);v.addView(status);Button run=new Button(this);run.setText("Review retained startup proposal");run.setOnClickListener(x->prepare());v.addView(run);Button refresh=new Button(this);refresh.setText("Refresh report");refresh.setOnClickListener(x->status.setText(last));v.addView(refresh);setContentView(v);}
 @Override protected void onStart(){super.onStart();stopped=false;status.setText(last);}
 private void say(String s){last=s;runOnUiThread(()->{if(!isDestroyed())status.setText(last);});}
 private void prepare(){if(blocked||!ACTIVE.compareAndSet(false,true)){say("Busy or previous uncertain fixture; no retry.");return;}final int g=generation;Context c=getApplicationContext();WORK.execute(()->{try{Fixture118 f=Fixture118.prepare(c);runOnUiThread(()->show(c,f,g));}catch(Exception|LinkageError e){blocked=true;ACTIVE.set(false);say("Preparation blocked; fixture retained. "+e.getClass().getSimpleName());}});}
 private void show(Context c,Fixture118 f,int g){if(stopped||g!=generation||isFinishing()||isDestroyed()){ACTIVE.set(false);say("Consent cancelled by lifecycle; no transaction.");return;}
  AtomicBoolean used=new AtomicBoolean();pending=used;Runnable cancel=()->{if(used.compareAndSet(false,true)){ACTIVE.set(false);say("Consent cancelled; no transaction.");}};
  dialog=new AlertDialog.Builder(this).setTitle("Review retained synthetic startup proposal").setMessage("Resource recovery complete: absent -> true\nLegacy signature detected: absent -> false\nRestored scene switches: absent -> []\nScene switch 101: absent -> []\n\nFixture only; no game launch.")
   .setNegativeButton("Cancel",(d,w)->cancel.run()).setPositiveButton("Confirm",(d,w)->{if(stopped||g!=generation||isFinishing()||isDestroyed()){cancel.run();return;}if(!used.compareAndSet(false,true))return;say("Confirmed; processing private fixture.");WORK.execute(()->{try{
      Fixture118.engine(c);Session117 s=new Session117(f.root.toPath(),Integer.toString(android.os.Process.myPid()),f.binding,f.expected,new ChaquopyTransport117(),Runnable::run);retained=s;s.complete(f.proposal(),f.binding);
      if(!"COMMITTED".equals(s.outcome))throw new java.io.IOException("Transaction unverified");retained=null;say("Reviewed startup transaction PASS (fixture only); runtime admission HOLD.");
     }catch(Exception|LinkageError e){blocked=true;say("Diagnostic BLOCKED; fixture retained. "+e.getClass().getSimpleName());}finally{ACTIVE.set(false);}});}).create();
  dialog.setOnCancelListener(d->cancel.run());dialog.setOnDismissListener(d->cancel.run());dialog.show();
 }
 @Override protected void onStop(){stopped=true;generation++;if(pending!=null&&pending.compareAndSet(false,true)){ACTIVE.set(false);say("Consent cancelled by lifecycle; no transaction.");}if(dialog!=null){dialog.dismiss();dialog=null;}super.onStop();}
 @Override protected void onDestroy(){if(dialog!=null){dialog.dismiss();dialog=null;}super.onDestroy();}
}
