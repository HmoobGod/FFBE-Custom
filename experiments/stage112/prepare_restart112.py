"""Inactive restart failure-path candidate, pinned upstream and retained gate shape."""
import hashlib, pathlib, sys
PIN='3f818845ed2e57b93498a6c8bece10a782da9522'
def stage(raw):
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=PIN: raise ValueError('wrong upstream blob')
    s=raw.decode('utf-8')
    def replace(old,new):
        nonlocal s
        if s.count(old)!=1: raise ValueError('unexpected source shape: '+old[:50])
        s=s.replace(old,new)
    replace('    private boolean installed;', '    private boolean installed;\n    private volatile boolean failed, destroyed;')
    replace('''        installed = state != null && state.getBoolean("installed");''','''        BootstrapAdmissionGate.requireGameplayAdmission();
        // Activity state is not a durable transaction receipt. Do not replay a handoff.
        if (state != null) { failed = true; return; }''')
    replace('        state.putBoolean("installed", installed); super.onSaveInstanceState(state);','        super.onSaveInstanceState(state);')
    replace('''        if (installed) { openGame(); return; }
        try {''','''        BootstrapAdmissionGate.requireGameplayAdmission();
        if (installed || failed || destroyed) return;
        try {''')
    replace('            if (getIntent().getBooleanExtra("delete", false)) SaveSlots.recoverDelete(this);','            if (destroyed || failed) return;\n            if (getIntent().getBooleanExtra("delete", false)) SaveSlots.recoverDelete(this);')
    replace('''        } catch (Exception error) {
            Log.e("SaveRestartActivity", error.getClass().getName() + ": " + error.getMessage(), error);
            // The next main-process initialization owns the existing recovery journals.
            openGame();
        }''','''        } catch (Exception | LinkageError error) {
            failed = true;
            Log.e("SaveRestartActivity", "Handoff stopped: " + error.getClass().getSimpleName());
            // Preserve recovery evidence. No automatic native launch or retry.
        }''')
    replace('''    private void openGame() {
        runOnUiThread(this::launchGame);''','''    private void openGame() {
        BootstrapAdmissionGate.requireGameplayAdmission();
        if (installed && !failed && !destroyed) runOnUiThread(this::launchGame);''')
    replace('''    private void launchGame() {
        try {''','''    private void launchGame() {
        BootstrapAdmissionGate.requireGameplayAdmission();
        if (!installed || failed || destroyed) return;
        try {''')
    replace('''            Log.e("SaveRestartActivity", error.getClass().getName() + ": " + error.getMessage(), error);
            finish();''','''            failed = true;
            Log.e("SaveRestartActivity", "Launch stopped: " + error.getClass().getSimpleName());''')
    replace('    @Override protected void onDestroy() { main.removeCallbacksAndMessages(null);', '    @Override protected void onDestroy() { destroyed = true; main.removeCallbacksAndMessages(null);')
    return s.encode('utf-8')
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('Usage: prepare_restart112.py UPSTREAM.java NEW.java')
    with pathlib.Path(sys.argv[2]).open('xb') as f: f.write(stage(pathlib.Path(sys.argv[1]).read_bytes()))
