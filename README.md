# FFBE-Custom

Independent public development repository for optional quality-of-life improvements to **Final Fantasy Brave Exvius Offline**.

## Origin and attribution

This project is based on the offline adaptation by Elvlin (https://github.com/Elvlin/exvius-offline)

- Source checkpoint: [`b520e563cbc4364a07ee40331012340dc8aeb841`](https://github.com/Elvlin/exvius-offline/commit/b520e563cbc4364a07ee40331012340dc8aeb841).
- `upstream-source`: source-only filtered history from that checkpoint (created by the import workflow).
- `develop`: separate QoL development branch based on the filtered source; retains the project-management baseline.
- `main`: documentation and import/test infrastructure, **not** a ready-to-install game build.

Git filtering necessarily changes commit hashes. Surviving commits retain original authorship, messages, dates and ancestry where applicable. The link above identifies the exact original unfiltered source revision.

**FFBE-Custom is unofficial, noncommercial, and not affiliated with or endorsed by Square Enix or gumi.** Final Fantasy Brave Exvius and its original characters, music, artwork, and other game content belong to their respective owners. Elvlin is credited for the original offline adaptation. Permission from the author does not imply authorization from third-party rightsholders.

## Public-repository safety

This repository is intentionally **public**. Its automated import is restricted to text code, build scripts, and documentation. It omits original game APKs, artwork, audio, downloadable data, game tables, extracted binaries, private saves, signing keys, and credentials.

Keep all of those excluded items out of issues, commits, Actions artifacts, and Releases. No APK publishing or installation is part of this setup. Source-only static checks do **not** prove the full game builds or runs.

## Workflows

- [Import permitted source](.github/workflows/import-permitted-source.yml): one-time source-only import from the pinned upstream revision; creates `upstream-source` and `develop` only when they do not already exist.
- [Source checks](.github/workflows/source-checks.yml): syntax, file allowlist and no-game-assets checks, including for future pull requests.

The complete original Android build is **not** provided by this repository: upstream's [build notes](https://github.com/Elvlin/exvius-offline/blob/main/source/README.md) require external tooling and a separately obtained verified original client. Those files are not committed here.

## Planned QoL development

After the source import is verified, scope changes in small, reversible pull requests. First priorities can be battle speed and repeat-battle options, roster sorting, and progression settings, subject to inspection of the actual code and save-compatibility tests.

Status: **initial bootstrap**. Do not assume imported branches, CI passing, a game build, or a playable APK until each has been separately verified.
