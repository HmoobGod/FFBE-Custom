#!/usr/bin/env python3
"""Verify and stage the private diagnostic118 sources and public-only build cache.
No network, signing, installation, or production profile access. Python 3.12+.
"""
import argparse, hashlib, json, pathlib, shutil, tarfile, zipfile, os, subprocess
P=pathlib.Path
SOURCE='10b8ea6c34a21e511d01b11b38889c8656907b859a204573744630facb05cd95'
COMPILE='cea42cbd3c384d1f4ddd96e17146c69f1f025eb36c893b809cb49cd83bcfdcd6'
RUNTIME='e3925bf43fd16bb35db7daea15416ddf645eb4d90c0a1ede53594265c44d8617'
PINS={'gradle.zip':'f6b8596b10cce501591e92f229816aa4046424f3b24d771751b06779d58c8ec4','platform.zip':'b32b10f787867987f03ae8e101d217e053a9065b7136379fb353b388379aed1d','build-tools.zip':'5d9ac77fb6ff43d9da518a337b4fcf8f9097113df531d99ccefe80ef7ce8250b','verification-metadata.xml':'02b0ce8a46c1cc2a71f7e520fda6aea48f735f167c4d00df2c7e35a2a0e5469e','stage107-dependencies.sha256':'569fe9d45bcf78685b30d4cd449d724046f19deed573659892608af7e3d3a789'}
def require(ok,msg):
    if not ok: raise ValueError(msg)
def sha(p):
    with P(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def h(b):return hashlib.sha256(b).hexdigest()
def pin(p,v):require(sha(p)==v,'Digest mismatch: '+str(p))
def zopen(p):
    z=zipfile.ZipFile(p);require(z.testzip() is None and len(set(z.namelist()))==len(z.namelist()),'Invalid ZIP');return z
def stage_source(src,compile_zip,out):
    pin(src,SOURCE);pin(compile_zip,COMPILE)
    with zopen(src) as z,zopen(compile_zip) as c:
        m=json.loads(z.read('evidence/members_sha256.json'));r=json.loads(c.read('actual-api-compile-receipt.json'))
        require(len(m)==76 and set(m)==set(z.namelist())-{'evidence/members_sha256.json'},'Source inventory')
        require(all(h(z.read(k))==v for k,v in m.items()),'Source member digest')
        require(len(r['classes'])==28 and all(h(c.read('classes/'+k))==v for k,v in r['classes'].items()),'Prior compiled classes')
        require(len(r['source_files'])==17 and all(m['diagnostic/src/main/java/'+k]==v for k,v in r['source_files'].items()),'Prior compiled source identity')
        for k in m:
            if k.startswith('diagnostic/'):
                p=out/k;require(p.resolve().is_relative_to(out.resolve()),'Unsafe source path');p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as f:f.write(z.read(k))
        print('Verified 76 members, 17 prior Java sources and 28 prior classes; staged exact diagnostic118 only.')
def read_hashes(p):
    rows={}
    for s in P(p).read_text().splitlines():
        digest,name=s.split('  ',1);require(len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'Digest format');require(name not in rows,'Duplicate digest name');rows[name]=digest
    return rows
def unpack_zip(src,out):
    # The three official ZIPs are pinned; system unzip preserves executable mode.
    with zopen(src) as z:
        require(all(not P(n).is_absolute() and '..' not in P(n).parts for n in z.namelist()),'ZIP paths')
    out.mkdir(parents=True,exist_ok=True);subprocess.run(['unzip','-q',str(src),'-d',str(out)],check=True)
def tar_extract(src,out):
    out.mkdir(parents=True,exist_ok=True)
    with tarfile.open(src,'r:*') as t:t.extractall(out,filter='data')
def stage_cache(parts,out,runtime):
    rows=read_hashes(parts/'parts.sha256');names=sorted(rows)
    require(names==[f'cache.part{i:02}' for i in range(len(names))] and 0<len(names)<=12,'Parts inventory')
    for n in names:pin(parts/n,rows[n])
    cache=out/'cache.tar'
    with cache.open('xb') as f:
        for n in names:
            with (parts/n).open('rb') as s:shutil.copyfileobj(s,f,1024*1024)
    pin(cache,read_hashes(parts/'cache.sha256')['cache.tar']);pack=out/'pack';tar_extract(cache,pack)
    files=read_hashes(parts/'files.sha256');require(set(files)=={p.name for p in pack.iterdir() if p.is_file()},'Pack inventory')
    for n,v in files.items():pin(pack/n,v)
    for n,v in PINS.items():pin(pack/n,v)
    unpack_zip(pack/'gradle.zip',out/'tools');unpack_zip(pack/'platform.zip',out/'platform');unpack_zip(pack/'build-tools.zip',out/'buildtools')
    (out/'sdk/platforms').mkdir(parents=True);(out/'sdk/build-tools').mkdir();shutil.move(out/'platform/android-13',out/'sdk/platforms/android-33');shutil.move(out/'buildtools/android-16',out/'sdk/build-tools/36.0.0')
    pin(out/'sdk/platforms/android-33/android.jar','fd628aa21321859a9035c6aae4b084b7d3fdb3f230be5cd5ec76541e32f7c963')
    tar_extract(pack/'jdk17.tar.gz',out/'jdk17');tar_extract(pack/'modules-2.tar.gz',out/'gradle-home/caches')
    prior=read_hashes(pack/'stage107-dependencies.sha256');current=read_hashes(pack/'dependencies.sha256');require(current and all(prior.get(k)==v for k,v in current.items()),'Unpinned dependency')
    deps=out/'gradle-home/caches/modules-2/files-2.1';require({str(p.relative_to(deps)) for p in deps.rglob('*') if p.is_file()}=={str(P(k)) for k in current},'Cache file inventory')
    for n,v in current.items():pin(deps/n,v)
    pin(runtime,RUNTIME)
    with zopen(runtime) as z:
        rt=out/'cpython310.tar.gz';rt.write_bytes(z.read('cpython310.tar.gz'))
    pin(rt,'5b6ae36e239727dd9b9c567023261e8b2fdd716d25dde2b15d68bf105b782856');tar_extract(rt,out/'tools')
    print('Verified all public tools, cache parts,',len(current),'dependency files, and existing CPython runtime.')
def main():
    a=argparse.ArgumentParser();a.add_argument('source',type=P);a.add_argument('compile',type=P);a.add_argument('destination',type=P);a.add_argument('--parts',type=P);a.add_argument('--runtime',type=P);x=a.parse_args();out=x.destination.resolve();out.mkdir(mode=0o700);stage_source(x.source,x.compile,out)
    if x.parts:
        require(x.runtime is not None,'Runtime required');stage_cache(x.parts,out,x.runtime)
if __name__=='__main__':main()
