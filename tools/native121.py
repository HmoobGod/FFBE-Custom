#!/usr/bin/env python3
"""Exact native-test candidate preflight and owner-local signing. No device writes."""
import argparse, hashlib, json, os, pathlib, re, struct, subprocess, tempfile, zipfile, shutil
P=pathlib.Path
APK_SHA='c36366552bc2f894278b902d16128625671572fa49bf3d3848f439b98a8a77bf'
JAR_SHA='3716d9311e55d2b0918a2fd9d54ba9e406c5f6abeea700b287f11259bc163dec'
CERT='f8be4d016081278f120faa30d80218da9c3edc52b538cfcaddb1bf0d82977654'
NATIVE='80587f3ade0ef736fc8e02ee6a4359a25d1b899cdea5322018a25176a3f573ca'
DEX='014d910828724d587ba0b296f06429f5c4946fada6f38e2ae084cae73af5a6c1'
MANIFEST='8fce5a30446ea87eead6300f52e4d64f0c3214dd1284c96ffe137bb3895a7d6a'
def require(ok,msg):
    if not ok: raise ValueError(msg)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def h(b):return hashlib.sha256(b).hexdigest()
def inventory(p):
    with zipfile.ZipFile(p) as z:
        require(z.testzip() is None and len(z.namelist())==3604 and len(set(z.namelist()))==3604,'APK inventory mismatch')
        return [(i.filename,i.compress_type,i.file_size,h(z.read(i))) for i in z.infolist()]
def run(args,**kwargs):return subprocess.run([str(a) for a in args],**kwargs)
def capture(args):return run(args,check=True,capture_output=True,text=True).stdout
def preflight(a):
    require(sha(a.apk)==APK_SHA,'Wrong Stage82 input APK')
    require(sha(a.jar)==JAR_SHA,'Wrong SDK36 signer JAR')
    rows=inventory(a.apk);d={n:s for n,_,_,s in rows}
    require(d['lib/arm64-v8a/libgame.so']==NATIVE and d['classes7.dex']==DEX and d['AndroidManifest.xml']==MANIFEST,'Pinned member mismatch')
    require(run([a.zipalign,'-c','4',a.apk],capture_output=True).returncode==0,'ZIP alignment failed')
    require(run([a.java,'-jar',a.jar,'verify',a.apk],capture_output=True).returncode!=0,'Input unexpectedly signed')
    badging=capture([a.aapt,'dump','badging',a.apk]);perms=capture([a.aapt,'dump','permissions',a.apk]);manifest=capture([a.aapt,'dump','xmltree',a.apk,'AndroidManifest.xml'])
    require("package: name='com.exvius.offline.test' versionCode='9089'" in badging and "native-code: 'arm64-v8a'" in badging and 'android.permission.INTERNET' not in perms,'Unexpected package or permissions')
    require('android:allowBackup(0x01010280)=(type 0x12)0x0' in manifest and 'android:extractNativeLibs(0x010104ea)=(type 0x12)0xffffffff' in manifest,'Unexpected manifest policy')
    align={};nonelf=[]
    with zipfile.ZipFile(a.apk) as z:
        for n in z.namelist():
            if not(n.startswith('lib/') and n.endswith('.so')):continue
            b=z.read(n)
            if b[:6]!=b'\x7fELF\x02\x01':nonelf.append(n);continue
            require(struct.unpack_from('<H',b,18)[0]==183,'Unexpected ELF machine')
            o=struct.unpack_from('<Q',b,32)[0];s,c=struct.unpack_from('<HH',b,54)
            require(s>=56 and o+c*s<=len(b),'ELF header bounds')
            v=[struct.unpack_from('<Q',b,o+i*s+48)[0] for i in range(c) if struct.unpack_from('<I',b,o+i*s)[0]==1]
            require(v and min(v)>=4096,'Unexpected PT_LOAD alignment');align[n]=min(v)
    require(set(nonelf)=={'lib/arm64-v8a/libexviustest.config.so','lib/arm64-v8a/libexviustest.js.so'},'Unexpected non-ELF payload')
    return rows,{'input_sha256':APK_SHA,'entries':len(rows),'package':'com.exvius.offline.test','versionCode':9089,'native_min_load_alignment':align,'non_elf_companion_payloads':nonelf,'recommended_native_trial_page_size':4096,'runtime_tested':False}
def verify_signed(a,p,rows):
    s=capture([a.java,'-jar',a.jar,'verify','--verbose','--print-certs',p]);require(re.search(r'(?m)^Verified using v2 scheme .*: true\s*$',s) and re.search(r'(?m)^Verified using v3 scheme .*: true\s*$',s),'Signature schemes missing')
    certs=re.findall(r'(?mi)^Signer #\d+ certificate SHA-256 digest: ([a-f0-9]{64})\s*$',s);require([c.lower() for c in certs]==[CERT],'Wrong permanent certificate')
    require(inventory(p)==rows,'Signed APK entry content/order/compression changed')
    require(run([a.zipalign,'-c','4',p],capture_output=True).returncode==0,'Signed alignment failed')
    return {'signed_sha256':sha(p),'certificate_sha256':CERT,'entries':len(rows),'v2':True,'v3':True,'alignment_4':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--apk',type=P,required=True);p.add_argument('--jar',type=P,required=True);p.add_argument('--zipalign',type=P,required=True);p.add_argument('--aapt',type=P,required=True);p.add_argument('--java',default='java');p.add_argument('--verify-signed',type=P);p.add_argument('--keystore',type=P);p.add_argument('--out',type=P);p.add_argument('--confirmed-backup',action='store_true');a=p.parse_args()
    rows,receipt=preflight(a)
    if a.verify_signed:
        require(not a.keystore and not a.out,'Select verify or signing');receipt.update(verify_signed(a,a.verify_signed,rows))
    elif a.keystore or a.out:
        require(a.keystore and a.out and a.confirmed_backup,'Owner backup confirmation and both signing paths required');require(a.keystore.is_file() and a.out.parent.is_dir(),'Missing signing paths');r=a.out.with_suffix(a.out.suffix+'.receipt.json');require(not a.out.exists() and not a.out.is_symlink() and not r.exists() and not r.is_symlink(),'Output exists');require(len({x.resolve() for x in (a.apk,a.jar,a.keystore,a.out,r)})==5,'Paths must be distinct')
        with tempfile.TemporaryDirectory(prefix='.ffbe-sign-',dir=a.out.parent) as t:
            s=P(t)/'signed.apk';run([a.java,'-jar',a.jar,'sign','--ks',a.keystore,'--ks-type','PKCS12','--ks-key-alias','ffbe-custom','--min-sdk-version','24','--v1-signing-enabled','false','--v2-signing-enabled','true','--v3-signing-enabled','true','--v4-signing-enabled','false','--out',s,a.apk],check=True)
            receipt.update(verify_signed(a,s,rows));require(sha(a.apk)==APK_SHA,'Original changed')
            with a.out.open('xb') as dest,s.open('rb') as src:shutil.copyfileobj(src,dest)
            require(sha(a.out)==receipt['signed_sha256'],'Signed output mismatch')
            with r.open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
