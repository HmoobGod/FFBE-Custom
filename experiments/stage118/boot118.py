"""Isolated diagnostic engine configuration. No live game init or player publication."""
import sys, os, pathlib, hashlib
_READY=None

def configure(engine):
    global _READY
    p=pathlib.Path(engine)
    if not p.is_absolute() or p.resolve(strict=True)!=p or not p.name.startswith('engine118-') or sys.version_info[:2]!=(3,10):
        raise RuntimeError('Isolated engine identity')
    if _READY is not None:
        if _READY!=p:raise RuntimeError('Engine already configured')
        return 'FIXTURE_ENGINE_READY'
    if any(n in sys.modules for n in ('player_state','data_paths','ffbe_state','local_game','capture_server')):raise RuntimeError('Engine already loaded')
    for n,expected in [('player_state.pyc','41f85022bad124f5a16d6ee75f9ad69364f715af265d84f9ca5325ee525d6436'),('data_paths.pyc','9a955e88f6aa6976257ad2fdbdc7aa0b0c00fe9edb8a71f56701d67c6b2044db')]:
        if hashlib.sha256((p/n).read_bytes()).hexdigest()!=expected:raise RuntimeError('Engine pin mismatch')
    os.environ.update(FFBE_DATA=str(p),MST_DIR=str(p/'mst_decoded'),TEXT_DIR=str(p/'text_decoded'),CDN_ROOT=str(p/'client/files'),CDN_OVERLAY=str(p/'overlay'),VERSION_TABLE_XML=str(p/'client/shared_prefs/gamedata.xml'),STATE_FILE=str(p/'never-live.json'),STATE_MODE='frozen',STATE='1',SEASON='off')
    sys.dont_write_bytecode=True;sys.path.insert(0,str(p))
    from bound90 import authentic_coherence
    import player_state, data_paths
    if pathlib.Path(player_state.__file__).parent!=p or pathlib.Path(data_paths.__file__).parent!=p or data_paths.MST_DIR!=str(p/'mst_decoded'):raise RuntimeError('Unexpected engine paths')
    authentic_coherence();_READY=p
    return 'FIXTURE_ENGINE_READY'
