"""Exercise the exact packaged local-game startup and title status, in disposable host data only."""
import sys,os,pathlib,hashlib,json,traceback
P=pathlib.Path;base=P(sys.argv[1]).resolve();static=base/'resources/exvius/data/static';root=P(sys.argv[2]).resolve(); mode=sys.argv[3]
if root.parent!=P('/tmp') or not root.name.startswith('ffbe122-case-') or root.stat().st_uid!=os.getuid() or mode not in ('ephemeral','live'):raise ValueError('Disposable root required')
files=root/'files'; writable=files/'exvius';writable.mkdir(parents=True,exist_ok=True)
os.environ.update(STATE_MODE=mode,SEASON='off',FFBE_CRYPTO='openssl',ENDPOINTS_FILE=str(base/'engine/endpoints.json'))
sys.dont_write_bytecode=True;sys.path.insert(0,str(base/'engine')); os.chdir(base/'engine')
def guard(event,args):
 if event.startswith('socket.') or event=='subprocess.Popen':raise RuntimeError('network/process denied')
 if event=='open' and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
  if not isinstance(args[0],(str,bytes,os.PathLike)) or not P(os.fsdecode(args[0])).resolve().is_relative_to(root):raise RuntimeError('write outside disposable root')
 if event in ('os.remove','os.rename','os.rmdir','os.mkdir','os.chmod','os.link','os.symlink','os.truncate'):
  for p in args[:2 if event in ('os.rename','os.link','os.symlink') else 1]:
   if not P(os.fsdecode(p)).resolve().is_relative_to(root):raise RuntimeError('mutation outside disposable root')
sys.addaudithook(guard)
import android_game
campaign=writable/'state/campaign.json'; before=campaign.read_bytes() if campaign.is_file() else None
g=android_game.start(str(writable),str(static));s=g.server.State
assert s.player is not None and len(s.replies)==49 and len(s.by_reqid)==220
print('PASS actual android_game.start: PlayerState, 49 replies, 220 request identities')
status=json.loads(android_game.title_action(g,'status'))
assert status['rank']==1 and status['has_save']==(mode=='live')
print('PASS actual title_action status', 'has_save='+str(status['has_save']), 'rank='+str(status['rank']))
r=android_game.request(g,'GET','/__exvius/status',b'','{}')
assert r.status==200 and json.loads(r.body)==status
print('PASS actual local GET status agrees with title_action')
if mode=='ephemeral':
 assert not campaign.exists();print('PASS ephemeral startup leaves no campaign')
else:
 assert campaign.is_file() and not campaign.is_symlink(); raw=campaign.read_bytes(); data=json.loads(raw);assert isinstance(data,dict) and data['rank']['level']==1
 print('PASS live disposable campaign persisted',hashlib.sha256(raw).hexdigest())
 if before is not None:
  assert json.loads(before)==data;print('PASS fresh campaign restart preserves semantic contents')
