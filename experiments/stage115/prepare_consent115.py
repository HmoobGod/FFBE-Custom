"""Bind Stage92-style one-shot review lifecycle to retained Stage114 proposal."""
import pathlib,hashlib,sys
P=pathlib.Path
raw=P(sys.argv[1]).read_bytes()
if hashlib.sha256(raw).hexdigest()!='8206aad360f8e65808d1c2065c568177526739f34fcf30c15d7075c6192d796d':raise ValueError('Wrong parent')
s=raw.decode();a='        byte[] takeFixture(Context c,String reviewedBinding) throws Exception {'
if s.count(a)!=1:raise ValueError('Wrong shape')
s=s.replace(a,'''        private boolean reviewIssued;
        synchronized Review115 reviewFixture(Context c) throws IOException {
            if(reviewIssued)throw new IOException("Review already issued");
            reviewIssued=true;return new Review115(this,c);
        }
        private byte[] takeFixture(Context c,String reviewedBinding) throws Exception {''')
a='    static synchronized Retained114 prepareDetached114('
if s.count(a)!=1:raise ValueError('Wrong shape')
s=s.replace(a,'''    // Stage92 one-shot review pattern; no production decision or startup authority.
    static final class Review115 {
        private final Retained114 retained;
        private final Context context;
        private boolean used;
        private Review115(Retained114 r,Context c){retained=r;context=Objects.requireNonNull(c);}
        String message(){return "Resource recovery complete: absent -> true\\nLegacy signature detected: absent -> false\\nRestored scene switches: absent -> []\\nScene switch 101: absent -> []\\n\\nSynthetic fixture only; no game launch.";}
        String binding(){return retained.binding;}
        synchronized byte[] acceptFixture()throws Exception {
            if(used)throw new IOException("Review consumed");used=true;
            return retained.takeFixture(context,retained.binding);
        }
        synchronized void cancel(){used=true;}
    }
'''+a)
with P(sys.argv[2]).open('x') as f:f.write(s)
