"""Host-only synthetic serializer compatibility probe. Never point at game saves.
Usage: python ffbe_stage108_fixture_probe.py <stage107-evidence.zip> <stage107-fixture.zip>
"""
import copy, hashlib, io, json, os, pathlib, sys, tempfile, types, zipfile

SOURCE_SHA='386b42fbc2dbcf1e318aa1565d97dab8fd2b175260b7c7e2268894e1e258799f'
FIXTURE_SHA='699d672234631ca17c6fdcb91b499087c3d78b2f8b813d90d8e0c916ff9bbd7a'
EVIDENCE_SHA='944060234f7542a47d4169a6ccb06bb4be8f218267d4dec1b9581a55a2a4d4fb'
BEFORE_SHA='0cd06e5243b656ec56fa4444ea641ac3a8e751b7329ec969aa27c40cd5e761ee'
AFTER_SHA='83175568cbcf4ac28e1fb2de96b94fe16cb51b5f24649de11658286ddcbed4b9'
def sha(b): return hashlib.sha256(b).hexdigest()
def require(ok):
    if not ok: raise RuntimeError('Fixture probe assertion failed')
def checked(raw, expected):
    require(sha(raw)==expected)
    z=zipfile.ZipFile(io.BytesIO(raw)); require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())))
    return z

def run(evidence, fixture):
    z=checked(pathlib.Path(evidence).read_bytes(), EVIDENCE_SHA)
    source=checked(z.read('source.zip'), SOURCE_SHA)
    f=checked(pathlib.Path(fixture).read_bytes(), FIXTURE_SHA)
    before, after=f.read('before.json'), f.read('after.json')
    require(sha(before)==BEFORE_SHA and sha(after)==AFTER_SHA)
    with tempfile.TemporaryDirectory(prefix='ffbe-stage108-') as t:
        root=pathlib.Path(t); modules=root/'modules'; modules.mkdir(mode=0o700)
        for name in ('coordinator88','first_write87','managed89','no_loss87','serializer106','strict87'):
            (modules/(name+'.py')).write_bytes(source.read('diagnostic/src/main/python/'+name+'.py'))
        sys.path.insert(0,str(modules))
        from strict87 import parse_campaign
        from serializer106 import _serialise, _SETS
        from managed89 import ManagedWriter, WriteBlocked
        from coordinator88 import Coordinator
        def parse(raw): return parse_campaign(raw,schema_version=2)
        a,b=parse(before),parse(after)
        expected=copy.deepcopy(a); expected['currencies']['gil']+=1
        require(expected==b and len(a)==25 and len(a['roster'])==2)
        def serialize(d): return json.dumps(_serialise(d),indent=1,ensure_ascii=True).encode('utf-8')
        def as_player(d):
            d=copy.deepcopy(d)
            for parent,key in _SETS: d[parent][key]={k:set(v) for k,v in d[parent][key].items()}
            return types.SimpleNamespace(data=d,dirty=False)
        require(serialize(as_player(a).data)==before and serialize(as_player(b).data)==after)
        print('PASS exact authentic serializer bytes roundtrip, 25 domains, two units, Gil-only delta')
        def coherence(d): return [] if d==a or d==b else ['outside pinned synthetic fixture pair']
        cat=b'{"format":1,"active":1,"slots":[{"id":1,"label":""}]}'
        def setup(tag):
            p=root/tag; p.mkdir(mode=0o700)
            for name in ('state','state/slots','prefs','files','later-writes'): (p/name).mkdir(mode=0o700)
            for name,data in [('state/campaign.json',before),('state/slots/index.json',cat),('prefs/gamedata.xml',b'<map/>')]:
                q=p/name; q.write_bytes(data); q.chmod(0o600)
            return p
        def writer(o):
            # A pre-existing synthetic fixture, not an admission or first-write proof.
            o.status='COMMITTED'; player=as_player(a); state=types.SimpleNamespace(player=player,state_dirty=False)
            return player,state,ManagedWriter(o,player,state,lambda p:serialize(p.data),coherence,fixture_authorized=True)
        p=setup('normal')
        with Coordinator(p) as o:
            player,state,w=writer(o); path=p/'state/campaign.json'; inode=path.stat().st_ino
            require(w.request('cdn_fetch',lambda:b'',fixture_authorized=True)==('NO_CHANGE',b''))
            require(path.read_bytes()==before and path.stat().st_ino==inode and not list((p/'later-writes').iterdir()))
            print('PASS authentic fixture HEAD-like no-change, inode and bytes preserved')
            def change():
                player.data['currencies']['gil']+=1; player.dirty=True; state.state_dirty=True; return b'ok'
            require(w.request('cdn_fetch',change,fixture_authorized=True)==('COMMITTED',b'ok'))
            tx=p/'later-writes/00000001'; rec=json.loads((tx/'committed.json').read_bytes())
            require(path.read_bytes()==after and (tx/'original.json').read_bytes()==before and (tx/'intent.json').read_bytes()==(tx/'committed.json').read_bytes() and not (tx/'proposed.tmp').exists())
            require(rec['original']==BEFORE_SHA and rec['proposed']==AFTER_SHA and rec['catalogue']==sha(cat) and rec['sequence']==1 and not player.dirty and not state.state_dirty and w.drain()=='DRAINED')
            require((p/'prefs/gamedata.xml').read_bytes()==b'<map/>' and not (p/'files/LKCBK.dat').exists())
            print('PASS actual Stage89 writer exact committed bytes and transaction record')
        p=setup('rejected')
        with Coordinator(p) as o:
            player,state,w=writer(o)
            def wrong(): player.data['currencies']['gil']+=2
            try: w.request('cdn_fetch',wrong,fixture_authorized=True)
            except WriteBlocked: pass
            else: raise RuntimeError('Unexpected write admission')
            require((p/'state/campaign.json').read_bytes()==before and not list((p/'later-writes').iterdir()) and w.status=='BLOCKED' and player.dirty and state.state_dirty)
            print('PASS out-of-pair mutation rejected before disk change')
        sys.path.remove(str(modules))
    print('4/4 PASS; host synthetic fixture only, no engine import or Android integration')
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit(__doc__)
    run(*sys.argv[1:])
