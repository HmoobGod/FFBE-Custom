"""Add inactive detached semantic inspection hook to exact Stage112 source."""
import hashlib,pathlib,sys
PIN='de4a35918518c1357d775fc8e8b301003b5acdfea72e1b9c48cb63082b42f983'
def stage(raw):
    if hashlib.sha256(raw).hexdigest()!=PIN:raise ValueError('Wrong Stage112 source')
    s=raw.decode(); anchor='    // Read-only profile validation, without claim or save initialization.'
    if s.count(anchor)!=1:raise ValueError('Wrong Stage112 shape')
    return s.replace(anchor,'''    interface DetachedInspector113 {
        // Host adapter only: must not start production Python or publish player.
        int inspect(byte[] campaign, String sha256) throws Exception;
    }
    static synchronized String detachedProfile113(Context c, DetachedInspector113 inspector) {
        String[] step = {"cold startup inspection"};
        try {
            cold112(c, step);
            ProfileInspection first = populatedCampaignSnapshot(c, step);
            step[0] = "detached campaign identity";
            File file = new File(c.getFilesDir().getCanonicalFile(), "exvius/state/campaign.json");
            byte[] campaign = readOwned(file, 8*1024*1024, false);
            if (!sha112(campaign).equals(first.campaignSha256)) throw new IOException("Campaign changed");
            cold112(c, step);
            step[0] = "detached semantic inspection";
            int changes = inspector.inspect(campaign, first.campaignSha256);
            if (changes < 0) throw new IOException("Semantic inspection rejected");
            cold112(c, step);
            ProfileInspection last = populatedCampaignSnapshot(c, step);
            cold112(c, step);
            step[0] = "profile evidence stability";
            if (!first.sameEvidence112(last)) throw new IOException("Profile evidence changed");
            return changes == 0 ? "Detached profile: NO_SEMANTIC_CHANGE; runtime admission HOLD"
                : "Detached profile: REVIEW_REQUIRED; runtime admission HOLD";
        } catch (Exception | LinkageError error) {
            return "Detached profile: BLOCKED at " + step[0] + ": " + error.getClass().getSimpleName();
        }
    }
'''+anchor).encode()
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: prepare113.py STAGE112.java NEW.java')
    with pathlib.Path(sys.argv[2]).open('xb') as f:f.write(stage(pathlib.Path(sys.argv[1]).read_bytes()))
