"""Read-only schema3 disposition: binds complete seven-target backup. No recovery writes."""
import json,re
from first_write87 import record, digest, classify_current, MANIFEST,BACKUP,COMMITTED,TEMP,open_dir,read_at
from coordinator88 import Blocked
import os

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def record116(intent,profile):
 if not isinstance(profile,str) or not re.fullmatch('[0-9a-f]{64}',profile):raise Blocked('Profile identity required')
 m=json.loads(record(intent));m.update(schema=3,profile=profile);return canonical(m)
def files(path):
 fd=open_dir(path)
 try:return {n:read_at(fd,n)[0] for n in os.listdir(fd)}
 finally:os.close(fd)
def inspect(o):
 from coordinator116 import TARGETS
 with o.mutex:
  o._owned();current=o._read_profile();pb,tb,stage=(files(o.root/k) for k in ('profile-backup','transaction-backup','staging'))
  try:
   m=json.loads(pb['manifest.json']);old={k:pb[f'{i}.bin'] if m[k] is not None else None for i,k in enumerate(TARGETS)}
   if set(m)!=set(TARGETS) or pb['manifest.json']!=canonical(m) or pb['complete.json']!=canonical(m) or m!=o._manifest(old) or set(pb)!={'manifest.json','complete.json'}|{f'{i}.bin' for i,k in enumerate(TARGETS) if old[k] is not None} or any(old[k]!=current[k] for k in TARGETS[1:]):raise ValueError()
   if not tb and not stage and old==current:return 'BACKUP_ONLY'
   if set(tb) not in ({MANIFEST,BACKUP},{MANIFEST,BACKUP,COMMITTED}) or tb[BACKUP]!=old[TARGETS[0]]:raise ValueError()
   raw=tb[MANIFEST];r=json.loads(raw)
   if set(r)!={'schema','original','proposed','catalogue','profile'} or r['schema']!=3 or raw!=canonical(r) or r['profile']!=digest(canonical(m)) or (COMMITTED in tb and tb[COMMITTED]!=raw):raise ValueError()
   legacy=dict(r);del legacy['profile'];legacy['schema']=2;legacy=json.dumps(legacy,sort_keys=True).encode()
   status=classify_current(current[TARGETS[0]],current[TARGETS[1]],legacy,tb[BACKUP],legacy if COMMITTED in tb else None)
   if stage and (status!='ORIGINAL_RETAINED' or set(stage)!={TEMP} or digest(stage[TEMP])!=r['proposed']):raise ValueError()
   o._owned();return status
  except (ValueError,KeyError,TypeError):return 'HOLD_UNKNOWN'
