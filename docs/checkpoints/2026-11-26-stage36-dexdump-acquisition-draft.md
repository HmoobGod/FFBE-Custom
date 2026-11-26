# Stage36 — dexdump acquisition draft (NOT ACTIVATED)

Derived from the successful public SDK-only workflow c088bc723c81cd3aec2419b68aedcf7e516fa83b, blob 81abaca282f7ba1e7b6e4c5b4d8559531962c021; run 45338825975, job 139699297065. Archive size, SHA1 and SHA256 taken from that job log. The workflow below is inert documentation, not installed or dispatched. Static scope checks only; workflow not run or independently YAML-validated. One separately authorized isolated lab branch workflow is the next action. No checkout, secrets, game inputs or game artifacts. If dexdump needs another library, stop and identify it from the authenticated archive before retrying. Negative fixture is only a launch/rejection smoke test, not proof of DEX validity. After acquiring tools and verifying hashes, locally run dexdump -c and dexdump -f on the exact approved primary DEX, preserve exit status/stderr/hash, and distinguish structural acceptance from Android runtime/class-linking verification. No private inputs in CI. All Stage36 HOLDs and flags retained; signing and installed signer choice unresolved. No game changes or test reruns.

```yaml
name: Stage36 public Android dexdump tools only
on:
  push:
    branches: [stage36-dexdump-tools-only-20261126]
    paths: ['.github/workflows/stage36-dexdump-tools-only.yml']
permissions: {}
jobs:
  transfer:
    if: github.event_name == 'push' && github.ref == 'refs/heads/stage36-dexdump-tools-only-20261126' && github.repository == 'HmoobGod/ffbe-rev13-metadata-lab'
    runs-on: ubuntu-24.04
    timeout-minutes: 8
    steps:
      - name: Fetch and authenticate public SDK archive
        shell: bash
        run: |
          set -euo pipefail
          cd "$RUNNER_TEMP"
          mkdir dexdump-tools-only
          cd dexdump-tools-only
          curl --fail --silent --show-error --location --proto '=https' --max-time 90 https://dl.google.com/android/repository/repository2-1.xml -o repository.xml
          python3 - <<'PY'
          import xml.etree.ElementTree as ET, json, re
          root=ET.parse('repository.xml').getroot()
          for e in root.iter():
              e.tag=e.tag.split('}')[-1]
          p=[p for p in root.findall('remotePackage') if p.attrib.get('path')=='build-tools;36.0.0']
          assert len(p)==1
          a=[a for a in p[0].findall('archives/archive') if a.findtext('host-os')=='linux']
          assert len(a)==1
          c=a[0].find('complete')
          name=c.findtext('url')
          digest=c.findtext('checksum')
          assert name == 'build-tools_r36_linux.zip',name
          assert re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',digest),digest
          data={'package':'build-tools;36.0.0','metadata_url':'https://dl.google.com/android/repository/repository2-1.xml','url':'https://dl.google.com/android/repository/'+name,'archive_size':int(c.findtext('size')),'archive_checksum':digest,'checksum_algorithm':'sha1' if len(digest)==40 else 'sha256'}
          open('origin.json','w').write(json.dumps(data,indent=2)+'\n')
          print(json.dumps(data))
          PY
          url="$(python3 -c 'import json;print(json.load(open("origin.json"))["url"])')"
          curl --fail --silent --show-error --location --proto '=https' --max-time 150 "$url" -o sdk.zip
          mkdir transfer
          python3 - <<'PY'
          import json, hashlib, pathlib, zipfile, os
          origin=json.load(open('origin.json'))
          b=pathlib.Path('sdk.zip').read_bytes()
          assert origin['archive_size']==63737259
          assert origin['checksum_algorithm']=='sha1'
          assert origin['archive_checksum']=='b0b6376977657e8ad9b969bacf4093601da2c6fb'
          assert len(b)==origin['archive_size']
          assert hashlib.new(origin['checksum_algorithm'],b).hexdigest()==origin['archive_checksum']
          origin['archive_sha256']=hashlib.sha256(b).hexdigest()
          assert origin['archive_sha256']=='5d9ac77fb6ff43d9da518a337b4fcf8f9097113df531d99ccefe80ef7ce8250b'
          with zipfile.ZipFile('sdk.zip') as z:
              assert z.testzip() is None
              for suffix in ['dexdump','source.properties','lib64/libc++.so']:
                  matches=[n for n in z.namelist() if n.endswith('/'+suffix) and n.count('/')==1+suffix.count('/')]
                  assert len(matches)==1,(suffix,matches)
                  p=pathlib.Path('transfer')/suffix
                  p.parent.mkdir(parents=True,exist_ok=True)
                  p.write_bytes(z.read(matches[0]))
          pathlib.Path('transfer/dexdump').chmod(0o755)
          origin['files']={str(p.relative_to('transfer')):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(pathlib.Path('transfer').rglob('*')) if p.is_file()}
          origin['workflow_commit']=os.environ['GITHUB_SHA']
          pathlib.Path('transfer/origin.json').write_text(json.dumps(origin,indent=2)+'\n')
          print(json.dumps(origin,indent=2))
          PY
          cd transfer
          grep -F 'Pkg.Revision=36.0.0' source.properties
          export LD_LIBRARY_PATH="$PWD/lib64"
          ldd ./dexdump | tee dependencies.txt
          if grep -q 'not found' dependencies.txt; then exit 1; fi
          # Negative smoke test: reject a synthetic non-DEX; no game input.
          printf 'not a dex file\n' > ../invalid.dex
          set +e
          ./dexdump -c ../invalid.dex > invalid-fixture.log 2>&1
          rc=$?
          set -e
          printf '%s\n' "$rc" > invalid-fixture-exit.txt
          test "$rc" -gt 0 && test "$rc" -lt 126
          grep -Ei 'dex|magic|open|error' invalid-fixture.log
          sha256sum dexdump lib64/libc++.so source.properties origin.json dependencies.txt invalid-fixture.log invalid-fixture-exit.txt > SHA256SUMS
          sha256sum -c SHA256SUMS
      - name: Transfer tools only
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: stage36-linux-dexdump-36
          path: ${{ runner.temp }}/dexdump-tools-only/transfer/
          if-no-files-found: error
          retention-days: 1
          compression-level: 6
```
