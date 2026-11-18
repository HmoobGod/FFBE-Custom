# Android build prerequisites and verification boundaries

This note is derived from the pinned upstream source checkpoint
[`b520e563cbc4364a07ee40331012340dc8aeb841`](https://github.com/Elvlin/exvius-offline/commit/b520e563cbc4364a07ee40331012340dc8aeb841)
and its [build documentation](https://github.com/Elvlin/exvius-offline/blob/b520e563cbc4364a07ee40331012340dc8aeb841/source/README.md).

## Upstream architecture

- `source/server/`: Python local game logic, persistence, request handling.
- `source/exvius/`: original-client integration, content reconstruction and release utilities.
- `source/memorial/android/`: Android local runtime/bootstrap integration.
- `source/harness/`: protocol and content-inspection utilities.
- `source/server_app/`: separate Rust/Python local-server developer application.

## Actual full Android build requirements

The upstream distribution build script targets **Windows** and requires:

- Java 11, Python 3.10, Node.js;
- Android SDK platform 33 and build-tools 36.0.0;
- Gradle 7.6.4 and Chaquopy 16.1.0;
- apktool 3.0.3 and arm64 Frida Gadget 17.24.3;
- environment variables `JAVA_HOME` and `ANDROID_HOME`;
- original verified Global v9.0.0 Android client, expected by upstream under
  `repository snapshots/FFBE-Global-v9.0.0-original.apk`, pinned upstream
  SHA-256 `955deacfbe4b3d0cd04e2947eb005e310915ba98132d71216626bfb3554ad246`;
- external vendor tools under `tools/vendor/` and private signing material
  controlled by the builder (the distribution script uses `EXVIUS_KEYSTORE_PASSWORD`).

Upstream `source/memorial/android/build.gradle` targets `arm64-v8a`, minSdk 24,
compileSdk/targetSdk 33, AGP 7.4.2, and Java 11.

**None of the original game APK, binary/art assets, data packages, private
keystores or vendor binaries are included in FFBE-Custom's public source-only
import.** The import intentionally omits JSON data tables and game content as
well. Consequently the code checkout is **not** a fully standalone Android
build; it cannot establish release readiness.

## Safe public CI implemented

- Check tracked files and historical paths against a conservative text-source
  allowlist, including a file-size/symlink gate.
- Compile Python syntax without running the game.
- Parse JavaScript syntax without executing the game.
- Run specifically selected synthetic/source-only unit tests only when added
  and independently verified to need no original game assets.
- Do **not** assemble an APK, download original client/data, create distributable
  artifacts, install an app, or publish releases.

## Next development gates

1. Define each requested QoL feature before editing original game logic.
2. Make changes on `develop` or a child branch, not `upstream-source`.
3. Require static checks, relevant fixture tests and save-compatibility review.
4. Treat Android/on-device confirmation as separately required and blocked
   until a rights-respecting local build/test procedure is approved.
