"""Stage111 private diagnostic109 workspace preparation, not a build or signing action."""
import hashlib, io, pathlib, sys, zipfile
SOURCE='c9573bb7795f6bc92e2f4322ed62c02bb4fb2bb2923b4129621328636007a5ec'
EVIDENCE='944060234f7542a47d4169a6ccb06bb4be8f218267d4dec1b9581a55a2a4d4fb'
VERIFY='02b0ce8a46c1cc2a71f7e520fda6aea48f735f167c4d00df2c7e35a2a0e5469e'
def sha(b): return hashlib.sha256(b).hexdigest()
def need(ok):
    if not ok: raise ValueError('Stage109 private input identity/layout mismatch')
def archive(path,pin):
    raw=pathlib.Path(path).read_bytes();need(sha(raw)==pin)
    z=zipfile.ZipFile(io.BytesIO(raw));need(z.testzip() is None and len(z.namelist())==len(set(z.namelist())))
    return z
def prepare(source,evidence,dest):
    s=archive(source,SOURCE); e=archive(evidence,EVIDENCE)
    data={n:s.read(n) for n in s.namelist()}
    need(len(data)==22 and all(n.startswith('diagnostic/') and '..' not in pathlib.PurePosixPath(n).parts and not n.endswith('/') for n in data))
    v=e.read('verification-metadata.xml');need(sha(v)==VERIFY)
    need('diagnostic/gradle/verification-metadata.xml' not in data)
    need(b'org.ffbe.diagnostic109' in data['diagnostic/build.gradle'])
    need(sha(data['diagnostic/src/main/assets/fixture109/before.json'])=='0cd06e5243b656ec56fa4444ea641ac3a8e751b7329ec969aa27c40cd5e761ee')
    need(sha(data['diagnostic/src/main/assets/fixture109/after.json'])=='83175568cbcf4ac28e1fb2de96b94fe16cb51b5f24649de11658286ddcbed4b9')
    data['diagnostic/gradle/verification-metadata.xml']=v
    data['evidence/stage107-dependencies.sha256']=e.read('dependencies.sha256')
    data['evidence/stage96-dependencies.sha256']=e.read('stage96-dependencies.sha256')
    dest=pathlib.Path(dest);dest.mkdir(mode=0o700,exist_ok=False)
    for n,b in data.items():
        p=dest/n;p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with p.open('xb') as out:out.write(b)
        p.chmod(0o600);need(p.read_bytes()==b)
    print(f'Private workspace ready: {len(data)} verified files; strict dependency metadata preserved. No build or execution.')
if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('Usage: prepare_private109.py SOURCE.zip STAGE107.zip NEW_PRIVATE_DIR')
    prepare(*sys.argv[1:])
