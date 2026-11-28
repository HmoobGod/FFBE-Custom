"""Exercise packaged encrypted user/home requests against a disposable local engine."""
import sys,os,pathlib,hashlib,json,traceback,re,stat
P=pathlib.Path;base=P(sys.argv[1]).resolve();static=P(sys.argv[4]).resolve();root=P(sys.argv[2]).resolve(); mode=sys.argv[3]
if root.parent!=P('/tmp') or not root.name.startswith('ffbe123-case-') or root.stat().st_uid!=os.getuid() or mode not in ('ephemeral','live'):raise ValueError('Disposable root required')
files=root/'files'; writable=files/'exvius';writable.mkdir(parents=True,exist_ok=True)
os.environ.update(STATE_MODE=mode,SEASON='off',FFBE_CRYPTO='openssl',ENDPOINTS_FILE=str(base/'engine/endpoints.json'))
sys.dont_write_bytecode=True;sys.path.insert(0,str(base/'engine')); os.chdir(base/'engine')
def guard(event,args):
 if event.startswith('socket.'):raise RuntimeError('network denied')
 if event=='subprocess.Popen':
  argv=args[1]; pattern=['openssl','enc']+(['-d'] if '-d' in argv else [])+['-aes-128-cbc','-nopad','-K',None,'-iv',None]
  if args[0]!='openssl' or len(argv)!=len(pattern) or any((a!=b if b is not None else re.fullmatch('[0-9a-f]{32}',a) is None) for a,b in zip(argv,pattern)):raise RuntimeError('subprocess denied')
 if event=='open' and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
  if isinstance(args[0],int) and stat.S_ISFIFO(os.fstat(args[0]).st_mode):return
  if not isinstance(args[0],(str,bytes,os.PathLike)) or not P(os.fsdecode(args[0])).resolve().is_relative_to(root):raise RuntimeError('write outside disposable root')
 if event in ('os.remove','os.rename','os.rmdir','os.mkdir','os.chmod','os.link','os.symlink','os.truncate'):
  for p in args[:2 if event in ('os.rename','os.link','os.symlink') else 1]:
   if not P(os.fsdecode(p)).resolve().is_relative_to(root):raise RuntimeError('mutation outside disposable root')
sys.addaudithook(guard)
import android_game,ffbe_crypto
from ffbe_crypto import cbc_encrypt,cbc_decrypt,key16,IV
campaign=writable/'state/campaign.json'
g=android_game.start(str(writable),str(static));s=g.server.State
mapping=json.loads((base/'engine/endpoints.json').read_bytes())['by_class']
assert (s.reply_key,s.reply_iv,s.double_pad,s.envelope,s.omit_header,s.echo_cipher)==('encodekey','literal',True,'obj',False,False)
classes=('GetUserInfoRequest','GetUserInfo2Request','GetUserInfo3Request','RoutineHomeUpdateRequest','FriendListRequest')
for i,cls in enumerate(classes,1):
 ep=mapping[cls];key=key16(ep['encode_key']);rid=ep['request_id'];body={'TEAYk6R1':{'z5hB3P01':rid},'t7n6cVWf':{'qrVcDe48':cbc_encrypt(key,b'{}',double_pad=False)}}
 r=android_game.request(g,'POST',ep['url'],json.dumps(body).encode(),'{}')
 assert r.status==200 and s.requests==i
 reply=json.loads(r.body);assert set(reply)=={'t7n6cVWf','TEAYk6R1'} and reply['TEAYk6R1']['z5hB3P01']==rid
 raw=cbc_decrypt(key,reply['t7n6cVWf']['qrVcDe48'],IV)
 pad=raw[-1];assert 1<=pad<=16 and raw[-pad:]==bytes([pad])*pad;raw=raw[:-pad]
 groups=json.loads(raw);data=s.player.data
 assert isinstance(groups,dict) and len(groups['LhVz6aD2'])==1 and groups['LhVz6aD2'][0]['m3Wghr1j']==s.player.friend_id()
 assert groups['J3pAG0I5']==[{'T7sah9rc':str(data['currencies']['lapis_free']),'cb3WmiD0':str(data['currencies']['lapis_paid'])}]
 assert groups['B71MekS8']==s.player.groups()['B71MekS8'] and len(groups['B71MekS8'])==2
 assert groups['5Eb0Rig6']==s.player.groups()['5Eb0Rig6']
 assert 'QB47tpMF' in groups if cls=='RoutineHomeUpdateRequest' else True
 assert groups['56gJBnVh']==[] if cls=='FriendListRequest' else True
 logs=list((campaign.parent/'requests').glob(f'*_{i:04d}.json'));assert len(logs)==1
 rec=json.loads(logs[0].read_bytes());assert rec['endpoint']['class']==cls and rec['selected_by']=='reqid' and rec['plaintext']=='{}' and rec['decrypt_error'] is None and rec['reply']['from_key']==rid and rec['reply']['body_plain_len']==len(raw) and rec['reply']['sha256_16']==hashlib.sha256(r.body).hexdigest()[:16]
 print('PASS',cls,'HTTP200, exact request mapping, decrypted envelope, roster/party/currency projection and request receipt;',len(groups),'groups')
assert json.loads(campaign.read_bytes())['rank']['level']==1
assert len(json.loads(campaign.read_bytes())['roster'])==2
print('PASS persisted rank and roster')
