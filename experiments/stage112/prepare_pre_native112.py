"""Apply a read-only pre-native profile inspection to the exact Stage84 candidate.
No production admission, launch, save writes or recovery are enabled.
"""
import hashlib, pathlib, sys
PIN='c03ebd36499d61b34dad461b6a9187a6e96475c594f5ccc223d83298c98067e1'
def stage(raw):
    if hashlib.sha256(raw).hexdigest()!=PIN: raise ValueError('wrong Stage84 source')
    s=raw.decode('utf-8')
    def replace(old,new):
        nonlocal s
        if s.count(old)!=1: raise ValueError('unexpected source shape: '+old[:50])
        s=s.replace(old,new)
    replace('static void claim() {','static synchronized void claim() {')
    replace('private static String singleCampaignOnly(File state, String[] step)', 'private static String[] singleCampaignOnly(File state, String[] step)')
    replace('''        byte[] hash = java.security.MessageDigest.getInstance("SHA-256").digest(campaign);
        StringBuilder digest = new StringBuilder(64);
        for (byte b : hash) digest.append(String.format(Locale.ROOT, "%02x", b & 0xff));
        return digest.toString();''','''        return new String[]{sha112(campaign), sha112(catalogue)};''')
    replace('''        ProfileInspection(ProfileKind kind, String campaignSha256) {
            this.kind = kind;
            this.campaignSha256 = campaignSha256;
        }''','''        final String catalogueSha256, registrySha256, preferencesSha256;
        ProfileInspection(ProfileKind kind, String campaignSha256, String catalogueSha256,
                          String registrySha256, String preferencesSha256) {
            this.kind = kind;
            this.campaignSha256 = campaignSha256;
            this.catalogueSha256 = catalogueSha256;
            this.registrySha256 = registrySha256;
            this.preferencesSha256 = preferencesSha256;
        }
        boolean sameEvidence112(ProfileInspection other) {
            return kind == other.kind && Objects.equals(campaignSha256, other.campaignSha256)
                && Objects.equals(catalogueSha256, other.catalogueSha256)
                && Objects.equals(registrySha256, other.registrySha256)
                && Objects.equals(preferencesSha256, other.preferencesSha256);
        }''')
    replace('        final String campaignSha256;\n        switch (scope)', '        final String campaignSha256, catalogueSha256;\n        switch (scope)')
    replace('                    ? ProfileKind.INITIAL_CATALOGUE : ProfileKind.FRESH;\n                campaignSha256 = null;', '                    ? ProfileKind.INITIAL_CATALOGUE : ProfileKind.FRESH;\n                campaignSha256 = null; catalogueSha256 = null;')
    replace('                campaignSha256 = singleCampaignOnly(new File(exvius, "state"), step);', '                String[] saveDigests = singleCampaignOnly(new File(exvius, "state"), step);\n                campaignSha256 = saveDigests[0]; catalogueSha256 = saveDigests[1];')
    replace('        JSONObject registry = new JSONObject(new String(readOwned(new File(exvius, "data/registry.json"), 1024*1024, false), StandardCharsets.UTF_8));', '        byte[] registryBytes = readOwned(new File(exvius, "data/registry.json"), 1024*1024, false);\n        JSONObject registry = new JSONObject(new String(registryBytes, StandardCharsets.UTF_8));')
    replace('        Element root = SaveTransferActivity.preferences(readOwned(new File(prefs, "gamedata.xml"), 1024*1024, true)).getDocumentElement();', '        byte[] preferenceBytes = readOwned(new File(prefs, "gamedata.xml"), 1024*1024, true);\n        Element root = SaveTransferActivity.preferences(preferenceBytes).getDocumentElement();')
    replace('        return new ProfileInspection(kind, campaignSha256);', '''        return new ProfileInspection(kind, campaignSha256, catalogueSha256,
                scope == InspectionScope.DIAGNOSTIC_POPULATED_ONLY ? sha112(registryBytes) : null,
                scope == InspectionScope.DIAGNOSTIC_POPULATED_ONLY ? sha112(preferenceBytes) : null);''')
    replace('    // Read-only profile validation, without claim or save initialization.', '''    private static String sha112(byte[] bytes) throws Exception {
        StringBuilder digest = new StringBuilder(64);
        for (byte b : java.security.MessageDigest.getInstance("SHA-256").digest(bytes))
            digest.append(String.format(Locale.ROOT, "%02x", b & 255));
        return digest.toString();
    }
    private static void cold112(Context c, String[] step) throws Exception {
        if (claimed || running || preparing != null) throw new IOException("Startup already claimed");
        checkPreflight(c, step);
    }
    // Inactive: cold main-process evidence, not a stopped-process witness or launch token.
    // Serialize against the existing claim method; no save initialization or Python start.
    static synchronized String preNativePopulatedInspection112(Context c) {
        String[] step = {"cold startup inspection"};
        try {
            cold112(c, step);
            ProfileInspection first = populatedCampaignSnapshot(c, step);
            cold112(c, step);
            ProfileInspection second = populatedCampaignSnapshot(c, step);
            cold112(c, step);
            step[0] = "profile evidence stability";
            if (!first.sameEvidence112(second)) throw new IOException("Profile evidence changed");
            return "Pre-native populated profile inspection: PASS; runtime admission HOLD";
        } catch (Exception | LinkageError error) {
            return "Pre-native populated profile inspection: BLOCKED at " + step[0] + ": " + error.getClass().getSimpleName();
        }
    }
    // Read-only profile validation, without claim or save initialization.''')
    return s.encode('utf-8')
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('Usage: prepare_pre_native112.py STAGE84.java NEW.java')
    with pathlib.Path(sys.argv[2]).open('xb') as f: f.write(stage(pathlib.Path(sys.argv[1]).read_bytes()))
