package com.exvius.local;

/** Inactive candidate: covers only registered Cocos workers and their MAIN callbacks.
 * Not a native/GL, preference, filesystem or full game-quiescence proof. */
final class CocosTaskDrain110 {
    interface Poster { boolean post(Runnable callback); }
    private int tasks;
    private boolean uncertain;
    private Lease held;

    synchronized Ticket begin() {
        if (held != null) throw new IllegalStateException("Cocos task drain held");
        if (tasks == Integer.MAX_VALUE) { uncertain = true; throw new IllegalStateException("Task count overflow"); }
        tasks++;
        return new Ticket();
    }
    synchronized Lease tryAcquire() {
        if (uncertain || tasks != 0 || held != null) return null;
        held = new Lease(Thread.currentThread());
        return held;
    }
    synchronized boolean idle() { return tasks == 0 && !uncertain; }
    synchronized boolean uncertain() { return uncertain; }
    private synchronized void fault() { uncertain = true; }

    final class Lease implements AutoCloseable {
        private final Thread owner;
        private Lease(Thread owner) { this.owner = owner; }
        public void close() {
            synchronized (CocosTaskDrain110.this) {
                if (held != this || owner != Thread.currentThread())
                    throw new IllegalStateException("Invalid Cocos drain release");
                if (uncertain) throw new IllegalStateException("Uncertain Cocos drain retained");
                held = null;
            }
        }
    }

    final class Ticket {
        private boolean workerDone, retired;
        private int pending;
        private Ticket() {}
        private void retireIfDone() { // parent monitor held
            if (workerDone && pending == 0 && !retired) { retired = true; tasks--; }
        }
        void workerFinished() {
            synchronized (CocosTaskDrain110.this) {
                if (workerDone) { fault(); throw new IllegalStateException("Duplicate worker completion"); }
                workerDone = true; retireIfDone();
            }
        }
        void workerFailed() { fault(); workerFinished(); }
        void post(Poster poster, Runnable callback) {
            if (poster == null || callback == null) throw new NullPointerException();
            final Posted work;
            synchronized (CocosTaskDrain110.this) {
                if (workerDone || pending == Integer.MAX_VALUE) {
                    fault(); throw new IllegalStateException("Invalid Cocos callback enqueue");
                }
                pending++; work = new Posted(callback);
            }
            // Do not hold the counter monitor while invoking a Handler or callback.
            // Failed/uncertain delivery is sticky; never claim an idle lease afterward.
            try {
                if (!poster.post(work)) throw new IllegalStateException("Cocos MAIN rejected callback");
            } catch (RuntimeException | Error failure) {
                fault(); throw failure;
            }
        }
        private final class Posted implements Runnable {
            private final Runnable callback;
            private boolean started;
            Posted(Runnable callback) { this.callback = callback; }
            public void run() {
                synchronized (CocosTaskDrain110.this) {
                    if (started) { fault(); throw new IllegalStateException("Duplicate Cocos callback"); }
                    started = true;
                }
                try { callback.run(); }
                catch (RuntimeException | Error failure) { fault(); throw failure; }
                finally {
                    synchronized (CocosTaskDrain110.this) { pending--; retireIfDone(); }
                }
            }
        }
    }
}
