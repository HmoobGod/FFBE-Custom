package com.exvius.local;
import java.util.ArrayDeque;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicReference;

final class CocosTaskDrain110Test {
    static void check(boolean ok) { if (!ok) throw new AssertionError(); }
    static void denied(Runnable r) { try { r.run(); } catch (IllegalStateException expected) { return; } throw new AssertionError("expected denial"); }
    static void pass(String label) { System.out.println("PASS " + label); }
    public static void main(String[] args) throws Exception {
        CocosTaskDrain110 a = new CocosTaskDrain110();
        ArrayDeque<Runnable> main = new ArrayDeque<>();
        CocosTaskDrain110.Ticket w = a.begin();
        w.post(main::offer, () -> {}); w.post(main::offer, () -> {});
        check(a.tryAcquire() == null); w.workerFinished();
        check(a.tryAcquire() == null); main.remove().run(); check(a.tryAcquire() == null);
        main.remove().run(); check(a.idle()); a.tryAcquire().close(); pass("worker exit does not hide queued start/progress/finish");
        CocosTaskDrain110 b = new CocosTaskDrain110();
        CocosTaskDrain110.Ticket parent = b.begin();
        AtomicReference<CocosTaskDrain110.Ticket> child = new AtomicReference<>();
        parent.post(main::offer, () -> { check(b.tryAcquire() == null); child.set(b.begin()); });
        parent.workerFinished(); main.remove().run(); check(b.tryAcquire() == null);
        child.get().workerFinished(); b.tryAcquire().close(); pass("runNextTask child keeps drain busy");
        CocosTaskDrain110 c = new CocosTaskDrain110();
        CocosTaskDrain110.Lease lease = c.tryAcquire(); check(lease != null); denied(c::begin); check(c.tryAcquire() == null);
        AtomicReference<Throwable> foreign = new AtomicReference<>();
        Thread stranger = new Thread(() -> { try { lease.close(); } catch (Throwable e) { foreign.set(e); } });
        stranger.start(); stranger.join(); check(foreign.get() instanceof IllegalStateException);
        denied(c::begin); lease.close(); denied(lease::close); c.begin().workerFinished(); pass("lease admission exclusion and same-thread release");
        CocosTaskDrain110 d = new CocosTaskDrain110(); CocosTaskDrain110.Ticket dw = d.begin();
        denied(() -> dw.post(r -> false, () -> {})); dw.workerFinished(); check(d.uncertain() && d.tryAcquire() == null); pass("Handler rejection retains uncertainty");
        CocosTaskDrain110 e = new CocosTaskDrain110(); CocosTaskDrain110.Ticket ew = e.begin();
        ew.post(main::offer, () -> { throw new IllegalStateException("callback failed"); }); ew.workerFinished();
        denied(main.remove()); check(e.uncertain() && e.tryAcquire() == null); pass("callback failure cannot grant drain");
        CocosTaskDrain110 f = new CocosTaskDrain110(); CocosTaskDrain110.Ticket fw = f.begin();
        fw.post(main::offer, () -> {}); Runnable repeat = main.remove(); repeat.run(); fw.workerFinished(); denied(repeat); check(f.uncertain() && f.tryAcquire() == null); pass("duplicate callback does not underflow");
        CocosTaskDrain110 g = new CocosTaskDrain110(); CocosTaskDrain110.Ticket gw = g.begin(); gw.workerFailed(); check(g.uncertain() && g.tryAcquire() == null); pass("worker start/failure uncertainty");
        CocosTaskDrain110 h = new CocosTaskDrain110(); CocosTaskDrain110.Ticket hw = h.begin();
        CountDownLatch reserved = new CountDownLatch(1), release = new CountDownLatch(1);
        AtomicReference<Runnable> pending = new AtomicReference<>(); AtomicReference<Throwable> threadError = new AtomicReference<>();
        Thread poster = new Thread(() -> { try { hw.post(r -> { pending.set(r); reserved.countDown(); try { release.await(); } catch (InterruptedException ex) { throw new AssertionError(ex); } return true; }, () -> {}); hw.workerFinished(); } catch(Throwable ex) { threadError.set(ex); } });
        poster.start(); reserved.await(); check(h.tryAcquire() == null); release.countDown(); poster.join(); check(threadError.get() == null && h.tryAcquire() == null); pending.get().run(); h.tryAcquire().close(); pass("actual concurrent enqueue/worker exit gap");
        System.out.println("8/8 PASS — scoped Java host fixture only");
    }
}
