import pathlib,hashlib,sys
P=pathlib.Path
p=P(sys.argv[1]);out=P(sys.argv[2]);
def get(n,h):
 b=(p/n).read_bytes()
 if hashlib.sha256(b).hexdigest()!=h:raise ValueError('Wrong parent')
 return b.decode()
def sub(s,a,b):
 if s.count(a)!=1:raise ValueError(a)
 return s.replace(a,b)
f=get('first_write115.py','8ab646df176684c8733a4a03f1a3a559e756fe9b03b61ddfde80e55b5d4177cb')
f=sub(f,'profile_witness=None):','profile_witness=None, profile_digest=None):')
f=sub(f,'manifest=record(intent)','manifest=record116(intent,profile_digest)')
f=sub(f,'from first_write87 import *','from first_write87 import *\nfrom records116 import record116')
c=get('coordinator115.py','3dc97960fdcfd4062057ccae1b2615e7818799671ec49f24e7cdeb3989fcd7ec')
c=sub(c,'from first_write115 import first_write','from first_write116 import first_write')
c=sub(c,'profile_witness=profile_witness)','profile_witness=profile_witness,profile_digest=integrity.profile)')
# Old cleanup explicitly not compatible with new schema. No mutation recovery enabled.
a=c.index('    def cleanup_fixture_staging(');c=c[:a]+"    def cleanup_fixture_staging(self,**_):raise Blocked('Schema3 inspection only')\n"
for n,s in [('first_write116.py',f),('coordinator116.py',c)]:
 with (out/n).open('x') as fp:fp.write(s)
