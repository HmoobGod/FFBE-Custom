"""Prepare inactive source adapter from the exact public upstream blob, never an APK."""
import hashlib
import pathlib
import sys

PIN = 'a3237cecab9d02a5024c159aea945dabc79bb7f8'

def stage(raw):
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=PIN:
        raise ValueError('Wrong LocalCocosTasks source blob')
    s=raw.decode('utf-8')
    def replace(old,new,n=1):
        nonlocal s
        if s.count(old)!=n: raise ValueError('Unexpected source shape: '+old[:40])
        s=s.replace(old,new)
    replace('    private LocalCocosTasks() {}', '''    private static final CocosTaskDrain110 DRAIN = new CocosTaskDrain110();

    // Scoped resource-task lease only. Do not call from production startup until
    // native GL, save writer/deleter, preferences and other ownership are proven.
    static CocosTaskDrain110.Lease tryAcquireTaskDrain110() { return DRAIN.tryAcquire(); }

    private static void removeWorker110(Object owner, Thread worker) {
        synchronized (ACTIVE) {
            Set<Thread> workers = ACTIVE.get(owner);
            if (workers != null) {
                workers.remove(worker);
                if (workers.isEmpty()) ACTIVE.remove(owner);
            }
        }
    }

    private LocalCocosTasks() {}''')
    replace('private static void progress(Object owner,', 'private static void progress(CocosTaskDrain110.Ticket ticket, Object owner,')
    replace('progress(owner,', 'progress(ticket, owner,',3)
    replace('MAIN.post(', 'ticket.post(MAIN::post, ',3)
    replace('        Thread worker = new Thread(() -> {', '''        final CocosTaskDrain110.Ticket ticket = DRAIN.begin();
        try {
        Thread worker = new Thread(() -> {
            try {''')
    replace('''                synchronized (ACTIVE) {
                    Set<Thread> workers = ACTIVE.get(owner);
                    if (workers != null) {
                        workers.remove(Thread.currentThread());
                        if (workers.isEmpty()) ACTIVE.remove(owner);
                    }
                }''', '                removeWorker110(owner, Thread.currentThread());')
    replace('''            }
        }, "ExviusLocalFile");''','''            }
            } catch (RuntimeException | Error failure) {
                removeWorker110(owner, Thread.currentThread());
                ticket.workerFailed();
                throw failure;
            }
            ticket.workerFinished();
        }, "ExviusLocalFile");''')
    replace('''        worker.start();
    }''','''        try { worker.start(); }
        catch (RuntimeException | Error failure) { removeWorker110(owner, worker); throw failure; }
        } catch (RuntimeException | Error failure) {
            ticket.workerFailed();
            throw failure;
        }
    }''')
    replace('''    public static void cancel(Object owner) {
        //''','''    public static void cancel(Object owner) {
        final CocosTaskDrain110.Ticket cancellation = DRAIN.begin();
        try {
        //''')
    replace('''            if (workers != null) for (Thread worker : workers) worker.interrupt();
        }
    }''','''            if (workers != null) for (Thread worker : workers) worker.interrupt();
        }
        } catch (RuntimeException | Error failure) {
            cancellation.workerFailed();
            throw failure;
        }
        cancellation.workerFinished();
    }''')
    return s.encode('utf-8')

if __name__ == '__main__':
    if len(sys.argv)!=3: raise SystemExit('Usage: stage_cocos_drain110.py UPSTREAM.java NEW.java')
    with pathlib.Path(sys.argv[2]).open('xb') as out: out.write(stage(pathlib.Path(sys.argv[1]).read_bytes()))
