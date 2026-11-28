"""Inactive experiment: charge original story-combat NRG at existing attempt boundary.
Only for host fixture integration until the native insufficient-energy response is verified.
"""
import copy, time

class InsufficientNRG(RuntimeError):
    pass

def install_fixture():
    import exvius_repeat as repeat
    import player_state as ps
    original = repeat.begin_attempt
    if getattr(original, '_story_nrg125', False):
        raise RuntimeError('Already installed')

    def begin_attempt(player, mid, captures=None):
        with repeat._LOCK:
            current = player.data.get('exvius_repeat', {}).get('attempt', {})
            if player.mode == 'frozen' or not mid or (current.get('mid') == str(mid) and current.get('status') == 'pending'):
                return original(player, mid, captures=captures)
            row = ps.mission_row(mid)
            world = ps._load_ndjson('F_WORLD_MST.ndjson', '9Pb24aSy').get(row.get('9Pb24aSy'), {}) if row else {}
            # Only main-story combat (existing main-story predicate and positive wave count).
            if not row or world.get('dw2nvP3r') != '1' or not (ps.mission_wave_count(mid) or 0):
                return original(player, mid, captures=captures)
            raw = row.get('B6kyCQ9M')
            if not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal():
                raise ValueError('Missing original mission NRG cost')
            cost = int(raw)
            if not cost:
                return original(player, mid, captures=captures)
            rank = player.data['rank']; saved = copy.deepcopy(rank); dirty = player.dirty
            if type(rank.get('nrg')) is not int or rank['nrg'] < 0:
                raise ValueError('Invalid NRG balance')
            now = int(time.time())
            balance = player.settle_nrg(now=now)
            if balance < cost:
                rank.clear(); rank.update(saved); player.dirty = dirty
                raise InsufficientNRG('Not enough NRG (fixture only; native error response unverified)')
            if not original(player, mid, captures=captures):
                rank.clear(); rank.update(saved); player.dirty = dirty
                return False
            # If energy was full/overfull, start a new regeneration interval upon crossing below cap.
            cap = ps.nrg_cap(rank['level'])
            rank['nrg'] = balance - cost
            if balance >= cap and rank['nrg'] < cap:
                rank['nrg_regen_anchor_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))
            player.data['exvius_repeat']['attempt']['nrg_cost'] = cost
            player.dirty = True
            return True
    begin_attempt._story_nrg125 = True
    repeat.begin_attempt = begin_attempt
    return original, begin_attempt
