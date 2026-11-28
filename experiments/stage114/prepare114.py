import pathlib,hashlib,sys
P=pathlib.Path
raw=P(sys.argv[1]).read_bytes()
assert hashlib.sha256(raw).hexdigest()=='e091b70b21a42b6f1e23eb22c2a69385f284e97c3e45217e013a76ec52a6297e'
s=raw.decode();anchor='    interface DetachedInspector113 {'
assert s.count(anchor)==1
s=s.replace(anchor,'''    interface ProposalInspector114 { byte[] inspect(byte[] original, String digest) throws Exception; }
    static final class Retained114 {
        private final ProfileInspection evidence;
        private final byte[] proposed;
        final String binding, proposalSha256;
        private boolean consumed;
        private Retained114(ProfileInspection e, byte[] original, byte[] p) throws Exception {
            evidence=e; proposed=p.clone(); proposalSha256=sha112(proposed);
            StartupReview114.verify(original, proposed);
            binding=sha112(("FFBE-STARTUP-FIXTURE-114\\n"+e.campaignSha256+"\\n"+e.catalogueSha256+"\\n"+e.registrySha256+"\\n"+e.preferencesSha256+"\\n"+proposalSha256).getBytes(StandardCharsets.UTF_8));
        }
        // Test-only one-shot transfer. Never a runtime launch or production write token.
        byte[] takeFixture(Context c,String reviewedBinding) throws Exception {
            synchronized(NativeStartupTrial.class) {
                if(consumed) throw new IOException("Proposal consumed");
                consumed=true;
                String[] step={"retained proposal"}; cold112(c,step);
                if(!binding.equals(reviewedBinding)||!evidence.sameEvidence112(populatedCampaignSnapshot(c,step))) throw new IOException("Stale review");
                cold112(c,step); return proposed.clone();
            }
        }
    }
    static synchronized Retained114 prepareDetached114(Context c, ProposalInspector114 inspector) throws Exception {
        String[] step={"cold proposal"}; cold112(c,step);
        ProfileInspection e=populatedCampaignSnapshot(c,step);
        byte[] old=readOwned(new File(c.getFilesDir().getCanonicalFile(),"exvius/state/campaign.json"),8*1024*1024,false);
        if(!sha112(old).equals(e.campaignSha256)) throw new IOException("Original changed");
        byte[] proposed=inspector.inspect(old.clone(),e.campaignSha256);
        Retained114 retained=new Retained114(e,old,proposed);
        cold112(c,step);
        if(!e.sameEvidence112(populatedCampaignSnapshot(c,step))) throw new IOException("Profile changed");
        cold112(c,step); return retained;
    }
'''+anchor)
P(sys.argv[2]).write_text(s)
