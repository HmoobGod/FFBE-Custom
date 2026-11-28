package com.exvius.local;

import java.io.IOException;

/** Inactive composition of registered GL/native operation and Cocos task scopes.
 * Not proof that original native code uses these scopes. */
final class OwnershipDrain111 implements PreferenceBoundary93.DrainWitness {
    private final CocosTaskDrain110 cocos, gl;
    private Thread owner;
    private CocosTaskDrain110.Lease cocosLease, glLease;
    private boolean blocked, completed;
    OwnershipDrain111(CocosTaskDrain110 cocos, CocosTaskDrain110 gl) {
        if (cocos == null || gl == null || cocos == gl) throw new IllegalArgumentException();
        this.cocos = cocos; this.gl = gl;
    }
    // Reserve before enqueue, not when GL starts running. No monitor held while posting.
    void postGl(CocosTaskDrain110.Poster poster, Runnable action) {
        CocosTaskDrain110.Ticket t = gl.begin();
        try { t.post(poster, action); }
        catch (RuntimeException | Error e) { t.workerFailed(); throw e; }
        t.workerFinished();
    }
    // For a registered synchronous native-facing writer or deleter only.
    void nativeOperation(Runnable action) {
        CocosTaskDrain110.Ticket t = gl.begin();
        try { action.run(); }
        catch (RuntimeException | Error e) { t.workerFailed(); throw e; }
        t.workerFinished();
    }
    private synchronized boolean acquire() {
        if (blocked || completed || owner != null) throw new IllegalStateException("Drain unavailable");
        glLease = gl.tryAcquire();
        if (glLease == null) return false;
        cocosLease = cocos.tryAcquire();
        if (cocosLease == null) {
            try { glLease.close(); glLease = null; }
            catch (RuntimeException | Error e) { blocked = true; throw e; }
            return false;
        }
        owner = Thread.currentThread(); return true;
    }
    public synchronized boolean quiescent() {
        return !blocked && !completed && owner == Thread.currentThread() &&
            glLease != null && cocosLease != null && gl.idle() && cocos.idle();
    }
    synchronized boolean blocked() { return blocked; }
    // Boundary must be constructed using this exact witness. A direct close without it fails.
    // Caller is a host fixture worker, never a UI/GL callback. No waiting on a busy scope.
    boolean closePreferences(PreferenceBoundary93 boundary) throws IOException {
        if (boundary == null || !boundary.usesDrainWitness(this)) throw new IllegalArgumentException("Wrong drain witness");
        if (!acquire()) return false;
        try {
            if (!quiescent()) throw new IOException("Scope uncertain");
            boundary.close();
            if (!quiescent()) throw new IOException("Scope changed after close; ownership uncertain");
            synchronized (this) {
                cocosLease.close(); cocosLease = null;
                glLease.close(); glLease = null;
                owner = null; completed = true;
            }
            return true;
        } catch (IOException | RuntimeException | Error e) {
            synchronized (this) { blocked = true; }
            throw e;
        }
    }
}
