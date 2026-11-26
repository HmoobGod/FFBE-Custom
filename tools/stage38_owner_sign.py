#!/usr/bin/env python3
"""Stage38 owner-local signing helper. Never creates or exports a private key."""
import argparse, hashlib, json, os, pathlib, re, subprocess, tempfile, zipfile
APK_SHA = "be09ed57b5c041dd31c6a6878dd3d9a7b7a665b0a77eb125151c604cd8c8c072"
JAR_SHA = "3716d9311e55d2b0918a2fd9d54ba9e406c5f6abeea700b287f11259bc163dec"
def require(ok, message):
    if not ok:
        raise SystemExit(message)
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def inventory(p):
    with zipfile.ZipFile(p) as z:
        require(z.testzip() is None, "ZIP CRC failure")
        rows = z.infolist()
        require(len({x.filename for x in rows}) == len(rows), "Duplicate ZIP member")
        return {x.filename: (x.compress_type, x.file_size, hashlib.sha256(z.read(x)).hexdigest()) for x in rows}
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apk", type=pathlib.Path, required=True)
    p.add_argument("--jar", type=pathlib.Path, required=True)
    p.add_argument("--zipalign", type=pathlib.Path, required=True)
    p.add_argument("--keystore", type=pathlib.Path, required=True)
    p.add_argument("--cert-sha256", required=True, help="Owner-verified certificate SHA256, no colons")
    p.add_argument("--out", type=pathlib.Path, required=True)
    p.add_argument("--confirmed-backup", action="store_true")
    p.add_argument("--authorize-signing", action="store_true")
    a = p.parse_args()
    require(a.confirmed_backup and a.authorize_signing, "Explicit owner signing and backup confirmations required")
    cert = a.cert_sha256.lower()
    require(re.fullmatch(r"[0-9a-f]{64}", cert), "Invalid certificate fingerprint")
    require(a.apk.is_file() and a.jar.is_file() and a.zipalign.is_file() and a.keystore.is_file(), "Missing required input")
    require(sha(a.apk) == APK_SHA, "Wrong unsigned APK")
    require(sha(a.jar) == JAR_SHA, "Wrong authenticated SDK36 apksigner jar")
    require(not a.out.exists() and not a.out.is_symlink(), "Output already exists")
    receipt = a.out.with_suffix(a.out.suffix + ".receipt.json")
    require(not receipt.exists() and not receipt.is_symlink(), "Receipt already exists")
    require(a.out.parent.is_dir(), "Output directory must exist")
    require(len({x.resolve() for x in [a.apk,a.jar,a.zipalign,a.keystore,a.out,receipt]}) == 6, "Paths must be distinct")
    # Use an official platform-specific zipalign binary installed by the owner.
    env = os.environ.copy()
    if os.name != "nt":
        libs = a.zipalign.resolve().parent / "lib64"
        if libs.is_dir():
            env["LD_LIBRARY_PATH"] = str(libs)
    def align(apk):
        subprocess.run([str(a.zipalign.resolve()), "-c", "4", str(apk.resolve())], check=True, env=env)
    before = inventory(a.apk)
    require(len(before) == 3604, "Unexpected APK member count")
    align(a.apk)
    # Private key stays on owner machine. apksigner prompts interactively; no password argument or log.
    with tempfile.TemporaryDirectory(prefix=".ffbe-sign-", dir=a.out.parent) as td:
        candidate = pathlib.Path(td) / "signed.apk"
        jar = ["java", "-jar", str(a.jar.resolve())]
        subprocess.run(jar + ["sign", "--ks", str(a.keystore.resolve()), "--ks-type", "PKCS12",
            "--ks-key-alias", "ffbe-custom", "--min-sdk-version", "24",
            "--v1-signing-enabled", "false", "--v2-signing-enabled", "true",
            "--v3-signing-enabled", "true", "--v4-signing-enabled", "false",
            "--out", str(candidate), str(a.apk.resolve())], check=True)
        v = subprocess.run(jar + ["verify", "--verbose", "--print-certs", str(candidate)],
                           check=True, capture_output=True, text=True)
        s = v.stdout
        require(re.search(r"(?m)^Verified using v2 scheme .*: true\s*$", s), "v2 signature not verified")
        require(re.search(r"(?m)^Verified using v3 scheme .*: true\s*$", s), "v3 signature not verified")
        require(re.search(r"(?m)^Number of signers: 1\s*$", s), "Unexpected signer count")
        found = re.findall(r"(?mi)^Signer #1 certificate SHA-256 digest: ([a-f0-9]{64})\s*$", s)
        require([x.lower() for x in found] == [cert], "Signer fingerprint mismatch")
        align(candidate)
        require(inventory(candidate) == before, "APK contents/compression changed")
        require(sha(a.apk) == APK_SHA, "Unsigned input changed")
        data = {"unsigned_sha256": APK_SHA, "signed_sha256": sha(candidate),
                "certificate_sha256": cert, "members": len(before),
                "v2": True, "v3": True, "alignment": "PASS",
                "runtime_tested": False, "installation_authorized": False}
        # Exclusive creation: no overwriting. Keep result only after verification.
        with a.out.open("xb") as f:
            with candidate.open("rb") as src:
                import shutil
                shutil.copyfileobj(src, f)
        require(sha(a.out) == data["signed_sha256"], "Output readback mismatch")
        with receipt.open("x", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(json.dumps(data, indent=2))
if __name__ == "__main__":
    main()
