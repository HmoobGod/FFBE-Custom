"""Inactive read-only semantic proposal handoff. Not an admission or write token."""
import hashlib, hmac, copy, json
from strict87 import parse_campaign, ExistingCampaignError
from no_loss87 import differences
from detached88 import detached_proposal

def sha(data): return hashlib.sha256(data).hexdigest()
def inspect(source, p, s, original, expected):
    if type(expected) is not str or not hmac.compare_digest(sha(original), expected):
        raise ExistingCampaignError('Campaign snapshot mismatch')
    before=parse_campaign(original,schema_version=2)
    def validate(data):
        if type(data['rank'].get('nrg')) is not int or data['rank']['nrg']<0:
            raise ExistingCampaignError('Negative or missing NRG')
        if p.state_coherence_issues(copy.deepcopy(data)):
            raise ExistingCampaignError('Campaign coherence failed')
    validate(before)
    prior=s.State.player
    proposed=detached_proposal(source,p,s,original)
    if s.State.player is not prior: raise ExistingCampaignError('Unexpected player publication')
    after=parse_campaign(proposed,schema_version=2);validate(after)
    changes=list(differences(before,after))
    # Proposal only. No auto approval, including a semantic no-op.
    return proposed, {'campaign_sha256':expected,'proposal_sha256':sha(proposed),
                      'changed_leaves':len(changes),'status':'REVIEW_REQUIRED' if changes else 'NO_SEMANTIC_CHANGE',
                      'runtime_admission':False}
