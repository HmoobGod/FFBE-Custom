"""Restore Stage109 isolated Android source from private Stage107 evidence and fixture.
Usage: python prepare_stage109.py evidence.zip fixture.zip NEW_DIRECTORY
Only the diagnostic is staged. Do not publish the resulting asset-bearing tree.
"""
import hashlib, io, pathlib, sys, zipfile

def sha(b): return hashlib.sha256(b).hexdigest()
def need(ok):
    if not ok: raise RuntimeError("Stage109 identity or layout mismatch")
def archive(raw, pin):
    need(sha(raw)==pin)
    z=zipfile.ZipFile(io.BytesIO(raw))
    need(z.testzip() is None and len(z.namelist())==len(set(z.namelist())))
    return z

def prepare(evidence, fixture, dest):
    z=archive(pathlib.Path(evidence).read_bytes(),'944060234f7542a47d4169a6ccb06bb4be8f218267d4dec1b9581a55a2a4d4fb')
    src=archive(z.read('source.zip'),'386b42fbc2dbcf1e318aa1565d97dab8fd2b175260b7c7e2268894e1e258799f')
    f=archive(pathlib.Path(fixture).read_bytes(),'699d672234631ca17c6fdcb91b499087c3d78b2f8b813d90d8e0c916ff9bbd7a')
    pins=['0cd06e5243b656ec56fa4444ea641ac3a8e751b7329ec969aa27c40cd5e761ee','83175568cbcf4ac28e1fb2de96b94fe16cb51b5f24649de11658286ddcbed4b9']
    snapshots=[f.read(n) for n in ('before.json','after.json')]
    need(all(len(b)==5995 and sha(b)==h for b,h in zip(snapshots,pins)))
    files={n:src.read(n) for n in src.namelist()}
    need(len(files)==20 and all(n.startswith('diagnostic/') and '..' not in pathlib.PurePosixPath(n).parts and not n.endswith('/') for n in files))
    p='diagnostic/src/main/'
    j=p+'java/org/ffbe/diagnostic95/'
    py=p+'python/managed106.py'
    s=files[py].decode().replace('import copy, json,','import hashlib, json,')
    start=s.index('# Source-shaped minimal');end=s.index('def allowed(',start)
    s=s[:start]+f'''# Pinned authentic synthetic fixture, never a user save. Java independently reads private assets.
BEFORE_SHA='{pins[0]}'
AFTER_SHA='{pins[1]}'
BEFORE_GIL=123456
AFTER_GIL=123457
def serialise(data):return json.dumps(_serialise(data),indent=1,ensure_ascii=True).encode('utf-8')
def digest(raw):return hashlib.sha256(raw).hexdigest()
def matches(data):
    g=data['currencies'].get('gil')
    return type(g) is int and g in (BEFORE_GIL,AFTER_GIL) and digest(serialise(data))==(BEFORE_SHA if g==BEFORE_GIL else AFTER_SHA)
'''+s[end:]
    s=s.replace('initial[TARGETS[0]]!=expected(8)','len(initial[TARGETS[0]])!=5995 or digest(initial[TARGETS[0]])!=BEFORE_SHA')
    s=s.replace("g=d['currencies'].get('gil');return [] if type(g) is int and g in (8,9) and serialise(d)==expected(g) else ['fixture mismatch']","return [] if matches(d) else ['fixture mismatch']")
    s=s.replace('w=ManagedWriter(o,player,state,',"if not matches(player.data):raise Blocked('Authentic serializer mismatch')\n        w=ManagedWriter(o,player,state,")
    files[py]=s.encode()
    d=j+'Disk95.java';s=files[d].decode();start=s.index('    static final String OLD=');end=s.index('    static void require',start)
    s=s[:start]+f'''    private static byte[][] fixture;
    static synchronized void loadFixture(android.content.Context app)throws Exception {{
        if(fixture!=null)return;
        byte[] before=readAsset(app,"before.json","{pins[0]}");
        byte[] after=readAsset(app,"after.json","{pins[1]}");
        fixture=new byte[][]{{before,after}};
    }}
    private static byte[] readAsset(android.content.Context app,String name,String pin)throws Exception {{
        try(InputStream in=app.getAssets().open("fixture109/"+name);ByteArrayOutputStream out=new ByteArrayOutputStream()){{
            byte[] buf=new byte[4096];int n;while((n=in.read(buf))!=-1){{require(out.size()+n<=5995);out.write(buf,0,n);}}
            byte[] data=out.toByteArray();require(data.length==5995&&pin.equals(digest(data)));return data;
        }}
    }}
    static synchronized byte[] before()throws IOException {{require(fixture!=null);return fixture[0].clone();}}
    static synchronized byte[] after()throws IOException {{require(fixture!=null);return fixture[1].clone();}}
'''+s[end:]
    files[d]=s.replace('digest(BEFORE)','digest(before())').replace('digest(AFTER)','digest(after())').encode()
    for name in ('DiagnosticActivity','Probe95','ManagedEndpoint106'):
        d=j+name+'.java';s=files[d].decode().replace('Disk95.BEFORE','Disk95.before()').replace('Disk95.AFTER','Disk95.after()')
        if name=='DiagnosticActivity':
            s=s.replace('File root=Disk95.root(app,id);','Disk95.loadFixture(app);File root=Disk95.root(app,id);',1)
        if name=='ManagedEndpoint106':
            s=s.replace('verify(root,before,Disk95.after(),true,injectFailure);Disk95.require','verify(root,before,Disk95.after(),true,false);Disk95.require').replace('&&gate.permit(root.getPath(),Process.myPid(),Process.myTid()));\n','&&gate.permit(root.getPath(),Process.myPid(),Process.myTid()));\n   if(injectFailure)throw new InjectedVerificationFailure();\n')
        files[d]=s.encode()
    for d in ['diagnostic/build.gradle',p+'AndroidManifest.xml']:
        files[d]=files[d].decode().replace('org.ffbe.diagnostic106','org.ffbe.diagnostic109').replace("versionName '106'","versionName '109'").replace('diagnostic 106','diagnostic 109').encode()
    expected={
        'diagnostic/build.gradle':'9f98e076e4300f82be2e5317b0fb1aa0d8dbf70c6f4052546e5724dc86719d08',
        p+'AndroidManifest.xml':'0752ab0e09a9074c799062e70e451b87fc77f7a3ee0d637d75a883d54897977c',
        j+'DiagnosticActivity.java':'3f4db938a71e591d5ae70010ceee0398537725dac28acc7f7d415d94435d93f0',
        j+'Disk95.java':'7db033fbbee0087a2082c85277460190aab9314d9061058ddf13a59ccf9c0a8e',
        j+'ManagedEndpoint106.java':'23e01cc36504c811b1cb9639df00602c9d22412f086657187a66d1cd72955732',
        j+'Probe95.java':'b4406ac06c69cbac592dbe17ce173c5ad37fd684aa2c0f0261af4245be534237',
        py:'3e2916054cc33082293ef2539bbdd640b5a170d5739fa126f0d3592474d3e92d'
    }
    need({n for n in files if files[n]!=src.read(n)}==set(expected))
    need(all(sha(files[n])==h for n,h in expected.items()))
    for n,b in zip(('before.json','after.json'),snapshots): files[p+'assets/fixture109/'+n]=b
    dest=pathlib.Path(dest)
    dest.mkdir(mode=0o700,parents=False,exist_ok=False)
    for n,b in files.items():
        q=dest/n;q.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        with q.open('xb') as out: out.write(b)
        q.chmod(0o600)
        need(q.read_bytes()==b)
    print('Stage109 restored: 7 exact changed source files, 13 retained, 2 private fixture assets.')
if __name__=='__main__':
    if len(sys.argv)!=4: raise SystemExit(__doc__)
    prepare(*sys.argv[1:])
