package com.exvius.local;
import java.nio.file.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;
final class OwnershipDrain111Test {
 static void ok(boolean b){if(!b)throw new AssertionError();}
 interface Action {void run()throws Exception;}
 static void denied(Action a)throws Exception{try{a.run();}catch(IllegalStateException|IOException|IllegalArgumentException e){return;}throw new AssertionError("allowed");}
 static final class Fixture {
  final CocosTaskDrain110 cocos=new CocosTaskDrain110(),gl=new CocosTaskDrain110();
  final OwnershipDrain111 scope=new OwnershipDrain111(cocos,gl);
  final Path root; final Supervisor91 owner; final TestPreference92.Fake g,c,a; final PreferenceBoundary93 boundary;
  Fixture()throws Exception {root=Files.createTempDirectory("ffbe111-test-");Files.createFile(root.resolve("writer.lock"));owner=new Supervisor91(root,new TestPreference92.EP(),true);owner.prepare(TestPreference92.A,TestPreference92.A);owner.confirm(owner.decideFixture(TestPreference92.A));g=new TestPreference92.Fake(root.resolve("g"));c=new TestPreference92.Fake(root.resolve("c"));a=new TestPreference92.Fake(root.resolve("a"));boundary=new PreferenceBoundary93(owner,g.prefs(),c.prefs(),a.prefs(),(s,v)->(s==PreferenceBoundary93.Store.GAMEDATA?g:s==PreferenceBoundary93.Store.COCOS?c:a).verify(v),scope,500);}
 }
 public static void main(String[] args)throws Exception{
  Fixture x=new Fixture(); ArrayDeque<Runnable> q=new ArrayDeque<>();x.scope.postGl(q::offer,()->{});ok(!x.scope.closePreferences(x.boundary)&&x.g.commits==0);q.remove().run();ok(x.scope.closePreferences(x.boundary)&&x.owner.state().equals("CLOSED"));System.out.println("PASS queued GL reservation prevents premature preference drain");
  Fixture y=new Fixture();CocosTaskDrain110.Ticket worker=y.cocos.begin();worker.post(q::offer,()->{});worker.workerFinished();ok(!y.scope.closePreferences(y.boundary)&&y.g.commits==0);y.scope.nativeOperation(()->{});q.remove().run();ok(y.scope.closePreferences(y.boundary));System.out.println("PASS pending Cocos callback prevents close; partial GL lease released");
  Fixture z=new Fixture();z.g.callback=()->{try {ok(z.scope.quiescent());denied(()->z.scope.nativeOperation(()->{throw new AssertionError();}));denied(()->z.cocos.begin());denied(()->z.scope.postGl(q::offer,()->{}));}catch(Exception e){throw new AssertionError(e);}};ok(z.scope.closePreferences(z.boundary));ok(z.g.commits==1&&z.c.commits==1&&z.a.commits==1);z.scope.nativeOperation(()->{});System.out.println("PASS held scopes exclude registered native writer/delete and enqueue throughout actual three-store commit/readback");
  Fixture f=new Fixture();f.g.failed=true;denied(()->f.scope.closePreferences(f.boundary));ok(f.scope.blocked()&&f.owner.state().equals("CONFIRMED"));denied(()->f.scope.nativeOperation(()->{}));denied(()->f.cocos.begin());denied(()->new Supervisor91(f.root,new TestPreference92.EP(),true));System.out.println("PASS failed preference commit retains file lock and scoped leases");
  Fixture w=new Fixture();denied(w.boundary::close);ok(w.g.commits==0&&w.boundary.failure()==null);Fixture other=new Fixture();denied(()->w.scope.closePreferences(other.boundary));ok(w.scope.closePreferences(w.boundary));ok(other.scope.closePreferences(other.boundary));System.out.println("PASS direct or foreign boundary close denied; correct witness succeeds");
  Fixture t=new Fixture();CountDownLatch started=new CountDownLatch(1),release=new CountDownLatch(1);Thread nativeThread=new Thread(()->t.scope.nativeOperation(()->{started.countDown();try{release.await();}catch(InterruptedException e){throw new AssertionError(e);}}));nativeThread.start();ok(started.await(2,TimeUnit.SECONDS));ok(!t.scope.closePreferences(t.boundary)&&t.g.commits==0);release.countDown();nativeThread.join();ok(t.scope.closePreferences(t.boundary));System.out.println("PASS actual concurrent registered native operation blocks drain until completion");
  System.out.println("6/6 PASS — host-only registered scopes, no native execution");
 }
}
