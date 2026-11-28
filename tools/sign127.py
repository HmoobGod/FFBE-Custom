#!/usr/bin/env python3
"""Owner-local launcher for the existing, pinned Stage126 signer. No key export or network."""
import argparse, os, pathlib, shutil, subprocess, sys
P=pathlib.Path
NAME='FFBE-Custom-9089-Zero-NRG-Stage126-UNSIGNED.apk'
OUT='FFBE-Custom-9089-Zero-NRG-Stage126-SIGNED.apk'
HERE=P(__file__).resolve().parent

def ask(label):
    return P(input(label+': ').strip().strip('"')).expanduser().resolve()

def first_file(paths):
    return next((p.resolve() for p in paths if p.is_file()),None)

def sdk_path(explicit):
    roots=[]
    if explicit: roots.append(explicit)
    else:
        for n in ('ANDROID_HOME','ANDROID_SDK_ROOT'):
            if os.environ.get(n): roots.append(P(os.environ[n]))
        if os.environ.get('LOCALAPPDATA'): roots.append(P(os.environ['LOCALAPPDATA'])/'Android/Sdk')
        roots += [HERE/'sdk',HERE]
    ext='.exe' if os.name=='nt' else ''
    for root in roots:
        for p in (root,root/'build-tools/36.0.0'):
            if all((p/f).is_file() for f in ('lib/apksigner.jar','aapt'+ext,'zipalign'+ext)):return p.resolve()
    if explicit:raise ValueError('SDK36 build-tools not found at supplied path')
    return sdk_path(ask('Path to your existing Android SDK or build-tools/36.0.0 folder'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--apk',type=P);p.add_argument('--sdk',type=P);p.add_argument('--java');p.add_argument('--keystore',type=P);p.add_argument('--out',type=P);p.add_argument('--preflight-only',action='store_true');a=p.parse_args()
    apk=a.apk or first_file([HERE/NAME,P.cwd()/NAME,P.home()/'Downloads'/NAME]) or ask('Path to exact unsigned Stage126 APK')
    sdk=sdk_path(a.sdk);ext='.exe' if os.name=='nt' else ''
    java=a.java or (str(P(os.environ['JAVA_HOME'])/'bin'/('java'+ext)) if os.environ.get('JAVA_HOME') and (P(os.environ['JAVA_HOME'])/'bin'/('java'+ext)).is_file() else shutil.which('java'))
    if not java:raise ValueError('Java 17 not found; use --java with your existing Java executable')
    cmd=[sys.executable,str(HERE/'native126.py'),'--apk',str(apk.resolve()),'--jar',str(sdk/'lib/apksigner.jar'),'--zipalign',str(sdk/('zipalign'+ext)),'--aapt',str(sdk/('aapt'+ext)),'--java',str(java)]
    if not a.preflight_only:
        if input('Confirm your original FFBE save is backed up (type YES): ').strip()!='YES':raise SystemExit('No signing performed')
        key=a.keystore or ask('Path to existing permanent FFBE PKCS12 keystore (do not upload it)')
        out=(a.out or apk.parent/OUT).resolve()
        cmd+=['--keystore',str(key.resolve()),'--out',str(out),'--confirmed-backup']
    subprocess.run(cmd,check=True)
    if not a.preflight_only:print('Verified signed APK and non-secret receipt saved next to the chosen output. Upload only those two files to private Drive.')
if __name__=='__main__':main()
