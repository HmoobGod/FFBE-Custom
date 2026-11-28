"""Host test entry. Standard input: exact validated campaign bytes; stdout: redacted report."""
import os, sys, pathlib, json, tempfile
from semantic113 import inspect
from strict87 import ExistingCampaignError,MAX_CAMPAIGN
P=pathlib.Path; base=P(sys.argv[1]).resolve(); resources=base/'resources/exvius/data/static'; root=P(tempfile.mkdtemp(prefix='ffbe113-'))
os.environ.update(FFBE_DATA=str(root),MST_DIR=str(resources/'mst_decoded'),TEXT_DIR=str(resources/'text_decoded'),CDN_ROOT=str(resources/'client/files'),CDN_OVERLAY=str(resources/'overlay'),VERSION_TABLE_XML=str(resources/'client/shared_prefs/gamedata.xml'),STATE_FILE=str(root/'campaign.json'),STATE_MODE='live',STATE='1',SEASON='off')
sys.dont_write_bytecode=True;sys.path.insert(0,str(base/'engine'))
def guard(event,args):
    if event.startswith('socket.') or event=='subprocess.Popen':raise RuntimeError('Network/subprocess denied')
    if event=='open' and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):raise RuntimeError('Write denied')
    if event in ('os.remove','os.rename','os.rmdir','os.mkdir','os.chmod','os.link','os.symlink','os.truncate'):raise RuntimeError('Filesystem mutation denied')
sys.addaudithook(guard)
try:
    import player_state as p, ffbe_state as s
    assert P(p.__file__).parent==base/'engine' and P(s.__file__).parent==base/'engine'
    before=sys.stdin.buffer.read(MAX_CAMPAIGN+1)
    _,report=inspect(base/'source',p,s,before,sys.argv[2]);print(json.dumps(report,separators=(',',':')))
except Exception as error:
    print(json.dumps({'status':'BLOCKED','kind':type(error).__name__,'runtime_admission':False}));sys.exit(2)
