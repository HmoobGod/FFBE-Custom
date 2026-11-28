package com.exvius.local;
import android.app.Activity;
import android.app.AlertDialog;
import java.util.Objects;
/** Stage92-style UI adapter for synthetic retained proposal. No production wiring. */
final class Consent115 {
 interface Completion {void complete(byte[] exactProposal,String binding);void denied();}
 private final NativeStartupTrial.Review115 review;
 private boolean done,shown;
 Consent115(NativeStartupTrial.Review115 r){review=Objects.requireNonNull(r);}
 private synchronized boolean finishOnce(){if(done)return false;done=true;return true;}
 private void deny(Completion c){if(finishOnce()){review.cancel();c.denied();}}
 void showFixture(Activity a,Completion c){
  synchronized(this){if(shown)throw new IllegalStateException("Review already displayed");shown=true;}
  a.runOnUiThread(()->{
   if(a.isFinishing()||a.isDestroyed()){deny(c);return;}
   new AlertDialog.Builder(a).setTitle("Review campaign changes (fixture)")
    .setMessage(review.message())
    .setNegativeButton("Cancel",(d,w)->deny(c)).setOnCancelListener(d->deny(c)).setOnDismissListener(d->deny(c))
    .setPositiveButton("Confirm",(d,w)->{
     if(a.isFinishing()||a.isDestroyed()){deny(c);return;}
     if(!finishOnce())return;
     byte[] bytes;
     try{bytes=review.acceptFixture();}catch(Exception e){c.denied();return;}
     c.complete(bytes,review.binding());
    }).show();
  });
 }
}
