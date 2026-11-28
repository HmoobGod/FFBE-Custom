"""Generate isolated registry-aware transaction siblings from pinned host sources."""
import hashlib, pathlib, sys
P=pathlib.Path

def checked(path,sha):
    raw=P(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Parent mismatch')
    return raw.decode()
def sub(s,a,b):
    if s.count(a)!=1:raise ValueError('Parent shape mismatch: '+a[:50])
    return s.replace(a,b)
def generate(parent,out):
    c=checked(parent/'coordinator88.py','3638ab31f70b11c6fc404167103a9018c9d29d4f213bb39de17a88548bf4bde5')
    f=checked(parent/'first_write87.py','33d6ab2a803de106d0012687e8a596bc5fab32224c7b3c4920fae5383ecee67f')
    f='''# Inactive sibling; shares original types and helpers.\nfrom first_write87 import *\n'''+f[f.index('def first_write('):]
    f=sub(f,'allow_first_write=False):','allow_first_write=False, profile_witness=None):')
    f=sub(f,'    d=b=t=slots=None; attempt=False','    if not callable(profile_witness):raise FirstWriteError("Registry-aware profile witness required")\n    d=b=t=slots=None; attempt=False')
    f=sub(f,'        attempt=True','        profile_witness(False)\n        attempt=True')
    f=sub(f,'        write_exclusive(b,COMMITTED,manifest)','        profile_witness(True)\n        write_exclusive(b,COMMITTED,manifest)\n        profile_witness(True)')
    c=sub(c,'from strict87 import ExistingCampaignSnapshot, _object','from first_write115 import first_write\nfrom strict87 import ExistingCampaignSnapshot, _object')
    c=sub(c,'class Blocked(RuntimeError): pass\n_registry=set(); _registry_lock=threading.Lock()','from coordinator88 import Blocked, _registry, _registry_lock')
    c=sub(c,"'files/LKCBK.dat')","'files/LKCBK.dat','data/registry.json')")
    c=sub(c,"('files',set(),{'LKCBK.dat'})]","('files',set(),{'LKCBK.dat'}),('data',{'registry.json'},set())]")
    c=sub(c,'                result=first_write(','''                def profile_witness(replaced):
                    expected=dict(d)
                    if replaced:expected[TARGETS[0]]=new
                    if self._read_profile()!=expected:raise Blocked('Profile changed at replacement boundary')
                    fd=open_dir(self.root/'profile-backup')
                    try:
                        m=canonical(self._manifest(d))
                        names={'manifest.json','complete.json'}|{f'{i}.bin' for i,k in enumerate(TARGETS) if d[k] is not None}
                        if set(os.listdir(fd))!=names or any(read_at(fd,n)[0]!=m for n in ('manifest.json','complete.json')) or any(read_at(fd,f'{i}.bin')[0]!=d[k] for i,k in enumerate(TARGETS) if d[k] is not None):raise Blocked('Backup changed at replacement boundary')
                    finally:os.close(fd)
                result=first_write(''')
    c=sub(c,'approved=approved,allow_first_write=True)','approved=approved,allow_first_write=True,profile_witness=profile_witness)')
    for n,s in [('first_write115.py',f),('coordinator115.py',c)]:
        with (out/n).open('x') as fp:fp.write(s)
if __name__=='__main__':generate(P(sys.argv[1]),P(sys.argv[2]))
