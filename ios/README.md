# 夜航 · iPhone MVP

Native SwiftUI app for iOS 17+, with no third-party iOS dependencies. Product: a quiet personal sleep-podcast library. API default is `https://alu-designer.pawlpixel.com/podcast/api`; login screen → 服务器 supports a different HTTPS endpoint or localhost HTTP for simulator development. Credentials live in Keychain, never in the project.

## Run

Open `NightHarbor.xcodeproj`, select the **NightHarbor** scheme and an iPhone simulator, then Run. The project now uses Zheng Fan's personal signing team `DXH9X9Y868`. Physical development installation requires a registered device and that team's signing access. TestFlight release status and commands are documented in `../docs/BETA-RELEASE.md`.

```sh
xcodebuild -project ios/NightHarbor.xcodeproj -scheme NightHarbor \
  -destination 'platform=iOS Simulator,id=4342D402-D677-4AC2-9BDA-062E8FB33957' \
  -derivedDataPath ios/build build-for-testing CODE_SIGN_IDENTITY=-
xcodebuild -project ios/NightHarbor.xcodeproj -scheme NightHarbor \
  -destination 'platform=iOS Simulator,id=4342D402-D677-4AC2-9BDA-062E8FB33957' \
  -derivedDataPath ios/build test-without-building CODE_SIGN_IDENTITY=-
```

Simulator builds must be ad-hoc signed (`CODE_SIGN_IDENTITY=-`) so Keychain works; do not disable code signing. The Xcode project is checked in. If adding/removing source files, `python3 ios/generate_project.py` regenerates it deterministically. `swift ios/make_icon.swift ios/NightHarbor/Assets.xcassets/AppIcon.appiconset/icon.png` regenerates the original native artwork icon.

## User journey

1. Register or log in with the same cloud account as the Web studio. The deployment may require an invite code.
2. Tonight offers the latest ready episode. An empty account presents a truthful empty state.
3. Create uses the included full Rainy Inn script. Set title, voice, ambience, or import/edit a version-1 JSON script. Saving creates a draft and does **not** generate billable audio.
4. Open a draft and confirm generation. The library polls actual server status every five seconds while foregrounded: draft → queued → generating → mixing → ready; errors, cancellation, retries, deletion and event history are visible.
5. The first play authenticates and downloads the audio to the account-specific local cache, then starts playback. Download explicitly for offline listening. MP3 production on the server keeps initial waiting smaller than WAV. This MVP does not stream partial audio while downloading.
6. The player supports pause, seek, ±15 seconds, background audio, lockscreen/remote controls, interruption/headphone-unplug pause, and timer off / 15 / 30 / 45 / 60 minutes / end of track. The final ten seconds of a timed stop fade out. An episode naturally stops at its end; there is no autoplay queue.
7. Position and completion sync to the server; failed progress updates persist for later retry. Metadata and audio caches are separated by API endpoint and account. Logout stops playback and hides that account’s cache. OS cache eviction remains possible. A successful cloud refresh removes locally cached items deleted on another device.

Voice/scene/ambience/timer preferences sync with the same account. Library polling stops when the app leaves the foreground; playback and progress can continue in audio background mode.

## Acceptance

Unit tests check JSON preservation/rejection, authenticated audio path/query construction without token URLs, API errors, and invalid media-time formatting. UI tests exercise onboarding and server settings. The live test is explicitly skipped unless dedicated credentials are injected; it signs in, creates and deletes a real draft, and can download/play a specified ready cloud podcast and background/foreground the app.

After the coordinator provisions a test account and generated podcast:

```sh
python3 ios/run_live_acceptance.py \
  --credentials-file .local/deployment-secrets.json \
  --ready-title 'the exact ready podcast title'
```

The helper reads `acceptance_password`, injects credentials only into a mode-0600 temporary `.xctestrun`, removes that file afterward, and keeps logs/results in ignored `ios/build/`. Treat `.xcresult` bundles as private test data; do not publish them. It never changes production App configuration or bundles credentials. DEBUG-only launch flags support `--uitest-reset`, `--api-base`, and `--uitest-offline`; release builds ignore these. The offline mode denies every URL loading request via a DEBUG-only URLProtocol, then verifies real previously downloaded files can play; it does not mock library/audio data. The live test finally logs out and verifies the cached library disappears.

Validation boundaries: simulator builds and runtime UI/playback checks do not constitute physical-device, overnight, TestFlight, App Store, or medical efficacy validation. iOS publication remains a separate step.

## Verified on 2026-10-02

Ad-hoc signed iPhone 17 Pro / iOS 26.2 simulator build passed. Six unit tests plus onboarding UI passed. The 89-second live production-API UI test passed: Keychain login, cloud draft creation/deletion, full 374.44-second MP3 download and playback, +15-second seek, three seconds in background with clock advancement, end-of-track selection, the real 20.24-second MCP episode naturally reaching 0:20 and stopping with the play button restored, app relaunch with all HTTP(S) requests denied and real cached playback advancing, and online logout hiding the cached library. The native player actually needed `.mp3` / `.wav` container extensions; that live-discovered issue is fixed and regression covered.

Safe evidence: `evidence/native-acceptance.json` and PNGs in `evidence/`. Minute-based timer expiry/fade and lockscreen remote buttons are implemented but were not directly exercised; the short-episode test proves natural completion/end-of-track stop only. No physical-device or release certification claim is made.
