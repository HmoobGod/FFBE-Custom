"""Isolated same-process startup fixture, not a production admission endpoint."""
import os, stat, threading, base64, hashlib
from pathlib import Path
from coordinator116 import Coordinator,TARGETS,Blocked
from records116 import inspect
from bound90 import BoundFixture
from no_loss87 import MISSING
from strict87 import MAX_CAMPAIGN
REVIEWED=((('exvius_resource_recovery','complete'),MISSING,True), (('exvius_resource_recovery','legacy_signature_detected'),MISSING,False), (('exvius_resource_recovery','restored_scene_switches'),MISSING,[]), (('progress','switches','101'),MISSING,[]))
sha=lambda b:hashlib.sha256(b).hexdigest()
_ACTIVE=threading.local()
class JavaOwned(Coordinator):
 def __init__(self,root,witness):
  super().__init__(root);self.witness=witness;self.thread=threading.get_ident();self.status='OWNED';s=root.lstat();self.rootid=(s.st_dev,s.st_ino);l=(root/'writer.lock').lstat();self.lockid=(l.st_dev,l.st_ino)
 def _owned(self):
  s=self.root.lstat();l=(self.root/'writer.lock').lstat()
  if self.pid!=os.getpid() or self.thread!=threading.get_ident() or (s.st_dev,s.st_ino)!=self.rootid or not stat.S_ISDIR(s.st_mode) or (l.st_dev,l.st_ino)!=self.lockid or not stat.S_ISREG(l.st_mode) or l.st_nlink!=1 or stat.S_IMODE(l.st_mode)!=0o600 or l.st_uid!=os.getuid() or not self.witness():raise Blocked('Java lease unavailable')
 def __enter__(self):raise Blocked('Java owns lease')
 def __exit__(self,*_):raise Blocked('Java owns lease')
def commit_fixture(root,pid,token,binding,proposal,witness):
 root=Path(root);proposal=bytes(proposal)
 if root.resolve(strict=True)!=root or not root.name.startswith('ffbe117-fixture-') or int(pid)!=os.getpid() or len(token)!=32 or len(proposal)>MAX_CAMPAIGN or getattr(_ACTIVE,'busy',False):raise Blocked('Fixture entry denied')
 _ACTIVE.busy=True
 try:
  o=JavaOwned(root,witness);d=o._read_profile()
  if any(d[k] is not None for k in TARGETS[3:6]):raise Blocked('Unexpected fixture data')
  expected=sha(('FFBE-STARTUP-FIXTURE-114\n'+'\n'.join(map(sha,(d[TARGETS[0]],d[TARGETS[1]],d[TARGETS[6]],d[TARGETS[2]],proposal)))).encode())
  if expected!=binding:raise Blocked('Review mismatch')
  b=BoundFixture(o,REVIEWED);t=b.prepare(sha(d[TARGETS[0]]),sha(d[TARGETS[1]]),proposal)
  b.commit_fixture(t,fixture_decision=True)
  if inspect(o)!='COMMIT_RECORDED':raise Blocked('Disposition mismatch')
  o._owned();return token+'\tCONFIRMED_FIXTURE_ONLY'
 finally:_ACTIVE.busy=False
# Chaquopy entry: exact Java bytes and only a read-only witness callback.
def commit_android(root,pid,token,binding,proposal,gate):
 return commit_fixture(root,pid,token,binding,proposal,gate.witness)
# Linux Stage94 JNI test adapter, same transaction body.
def request_fixture(root,pid,token,binding,encoded):
 import owner94
 return commit_fixture(root,pid,token,binding,base64.b64decode(encoded,validate=True),owner94.witness)
