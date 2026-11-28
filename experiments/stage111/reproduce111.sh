#!/usr/bin/env bash
# Usage: bash reproduce111.sh STAGE91.zip STAGE92.zip STAGE93A.zip
# Host-only fixtures. No game or Android execution.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python3 - "$1" "$2" "$3" "$work" <<'PY'
import hashlib, pathlib, sys, zipfile
pins=['efcc9c8c80a9d3c5372371611956f2c14ee7543f59bd16c7fb1b31961e5c48b1','4bf65c44b77037ecad92455030bb9fa903cdf1171da401139b20a1bbb56e3914','7dd1132ee1f5d78f3970ac949b4e76797491a509ea9fe17adc51715204ffa9f9']
z=[]
for path,pin in zip(sys.argv[1:4],pins):
    if hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()!=pin:raise ValueError('Wrong archive')
    f=zipfile.ZipFile(path)
    if f.testzip() is not None:raise ValueError('CRC')
    z.append(f)
w=pathlib.Path(sys.argv[4])
(w/'Supervisor91.java').write_bytes(z[0].read('Supervisor91.java'))
s=z[2].read('src/PreferenceBoundary93.java').decode()
old=' Outcome failure(){'
if s.count(old)!=1:raise ValueError('Wrong source shape')
s=s.replace(old,' boolean usesDrainWitness(DrainWitness witness){return drain==witness;}\n'+old)
(w/'PreferenceBoundary93.java').write_text(s)
s=z[1].read('src/TestPreference92.java').decode()
s=s[:s.index(' static class C {')].replace('catch(PreferenceBoundary92.WriteFailure|IOException expected)','catch(PreferenceBoundary93.WriteFailure|IOException expected)')+'}\n'
(w/'TestPreference92.java').write_text(s)
PY
mkdir -p "$work/stubs/android/content" "$work/stubs/com/chaquo/python" "$work/stubs/com/exvius/local"
cat > "$work/stubs/android/content/SharedPreferences.java" <<'EOF'
package android.content;
import java.util.Map;
public interface SharedPreferences { Map<String,?> getAll(); Editor edit();
 interface Editor { Editor putString(String k,String v); Editor putBoolean(String k,boolean v); Editor putInt(String k,int v); Editor putFloat(String k,float v); Editor remove(String k); boolean commit(); }
}
EOF
cat > "$work/stubs/com/chaquo/python/PyObject.java" <<'EOF'
package com.chaquo.python; public class PyObject { public PyObject callAttr(String n,Object... args){throw new UnsupportedOperationException();} }
EOF
cat > "$work/stubs/com/exvius/local/CatalogueHandoff91.java" <<'EOF'
package com.exvius.local; final class CatalogueHandoff91 { static String prepareFixture(Supervisor91 s){throw new UnsupportedOperationException();} }
EOF
javac -d "$work/classes" "$here/../stage110/CocosTaskDrain110.java" "$here/OwnershipDrain111.java" "$here/OwnershipDrain111Test.java" "$work/"*.java $(find "$work/stubs" -name '*.java')
java -cp "$work/classes" com.exvius.local.OwnershipDrain111Test
