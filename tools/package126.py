#!/usr/bin/env python3
"""Derive a zero-NRG-cost native candidate from the exact Stage124 APK."""
import argparse, hashlib, pathlib, struct, zipfile, copy, tempfile, subprocess, shutil, json
P=pathlib.Path
BASE='4e82912ee7e414f1b0f854f1b0adc264db8850ad302d3abe830db91771793446'
LIBSHA='80587f3ade0ef736fc8e02ee6a4359a25d1b899cdea5322018a25176a3f573ca'
LIB='lib/arm64-v8a/libgame.so'
OFF=0x1a78c64
OLD=bytes.fromhex('080500511f05007168000054')
NEW=bytes.fromhex('880200341f09007168000054')
def require(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def h(b):return hashlib.sha256(b).hexdigest()
def inventory(z):
    require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())),'ZIP integrity')
    return [(i.filename,i.compress_type,i.file_size,h(z.read(i))) for i in z.infolist()]
def patch(raw):
    require(h(raw)==LIBSHA and raw[:6]==b'\x7fELF\x02\x01','Wrong native library')
    require(struct.unpack_from('<H',raw,18)[0]==183,'Wrong architecture')
    off=struct.unpack_from('<Q',raw,32)[0];size,num=struct.unpack_from('<HH',raw,54)
    require(size==56 and any(t==1 and flags&1 and po==va==0 and OFF+len(OLD)<=fs for t,flags,po,va,pa,fs,ms,al in (struct.unpack_from('<IIQQQQQQ',raw,off+i*size) for i in range(num))),'Executable address mapping')
    require(raw[OFF:OFF+12]==OLD and raw[0x1a78cb4:0x1a78cbc]==bytes.fromhex('f3031f2ae003132a'),'Wrong native control flow')
    # parser literals and native cost icons corroborate the discriminator
    for offset,token in [(0x2f486cf,b'CQN15Hgr\0'),(0x2f2625f,b'B6kyCQ9M\0'),(0x2f38714,b'quest_stamina.png\0'),(0x2f38726,b'quest_raid_orbcost.png\0'),(0x2f3873d,b'tfa_raid_orb_prple.png\0')]:
        require(raw[offset:offset+len(token)]==token,'Cost type provenance mismatch')
    out=raw[:OFF]+NEW+raw[OFF+len(OLD):]
    require(len(out)==len(raw) and out[:OFF]==raw[:OFF] and out[OFF+12:]==raw[OFF+12:],'Unexpected native change')
    return out

def run(a):
    require(sha(a.base)==BASE,'Wrong parent APK')
    require(not a.out.exists() and not a.receipt.exists() and not a.out.is_symlink() and not a.receipt.is_symlink(),'Output exists')
    with zipfile.ZipFile(a.base) as z:
        before=inventory(z);require(len(before)==3604,'Unexpected parent inventory');raw=z.read(LIB);new=patch(raw)
        with tempfile.TemporaryDirectory(prefix='ffbe126-package-') as tmp:
            unaligned=P(tmp)/'raw.apk';aligned=P(tmp)/'aligned.apk'
            with zipfile.ZipFile(unaligned,'w',allowZip64=True) as dst:
                dst.comment=z.comment
                for i in z.infolist():dst.writestr(copy.copy(i),new if i.filename==LIB else z.read(i))
            subprocess.run([str(a.zipalign),'-f','4',str(unaligned),str(aligned)],check=True)
            subprocess.run([str(a.zipalign),'-c','4',str(aligned)],check=True)
            r=subprocess.run([str(a.java),'-jar',str(a.signer),'verify','--verbose',str(aligned)],capture_output=True,text=True)
            require(r.returncode!=0 and 'DOES NOT VERIFY' in r.stderr+r.stdout,'Expected unsigned APK')
            with zipfile.ZipFile(aligned) as out:
                after=inventory(out);require(len(after)==len(before) and [(x[0],x[1],x[2]) for x in before]==[(x[0],x[1],x[2]) for x in after],'APK member shape changed')
                require([x[0] for x,y in zip(before,after) if x!=y]==[LIB] and out.read(LIB)==new,'Unexpected APK content delta')
            with a.out.open('xb') as dst,aligned.open('rb') as src:shutil.copyfileobj(src,dst)
    require(sha(a.base)==BASE,'Parent changed')
    receipt={'parent':BASE,'apk_sha256':sha(a.out),'size':a.out.stat().st_size,'native_sha256':h(new),'native_offset':hex(OFF),'old':OLD.hex(),'new':NEW.hex(),'entries':3604,'unchanged':3603,'alignment4':True,'unsigned':True,'native_runtime_tested':False,'scope':'MissionUtil cost type 0 only; other cost types keep original branch behavior'}
    with a.receipt.open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('base',type=P);p.add_argument('out',type=P);p.add_argument('receipt',type=P);p.add_argument('--zipalign',type=P,required=True);p.add_argument('--signer',type=P,required=True);p.add_argument('--java',type=P,required=True);run(p.parse_args())
