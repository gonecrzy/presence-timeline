# Android App

This directory contains the Android-first parent app scaffold for `GpsTrack`.

## Current scope

- Package id: `com.gonecrzy.gpstrack`
- Auth mode: open development mode only
- Backend target: configurable local or public `GpsTrack API` base URL
- Screens:
  - family members list
  - live map shell
  - member detail with timeline and trip summaries
  - places management
  - settings

## Local setup

1. Install Android Studio and a matching Android SDK.
2. Copy the example file:

```bash
cp local.properties.example local.properties
```

3. Adjust the values to your backend:

```properties
sdk.dir=/path/to/Android/Sdk
gpstrack.baseUrl=http://192.168.1.50:18000/
gpstrack.mapStyleUrl=https://demotiles.maplibre.org/style.json
```

4. Open the `android/` directory in Android Studio or run:

```bash
./gradlew assembleDebug
```

## Release targets

Do not commit built APK files into git history.

Use git-hosted release artifacts instead:

1. Build a release APK with `./gradlew assembleRelease`
2. Sign it with your release keystore
3. Attach the generated APK to a tagged release on your git server

That keeps source history clean while still allowing direct APK download for parents.

## Manual Gitea upload

On this host, the Gitea API token used for release uploads is already stored outside this repo in `/root/bifrost/.env` as `REGISTRY_TOKEN`.

Related values in that same file:

- `GITEA_URL=https://git.home.gonecrzy.com`
- `REGISTRY_OWNER=gonecrzy69`

Do not copy the token into this repo or print it into logs. Rotate it in Gitea if it is ever exposed.

Typical manual upload flow:

1. Build the APK you want to publish:

```bash
./gradlew assembleDebug
```

2. Load the token and server settings:

```bash
set -a
. /root/bifrost/.env
set +a
```

3. Inspect existing releases:

```bash
curl -sk -H "Authorization: token $REGISTRY_TOKEN" \
  "${GITEA_URL%/}/api/v1/repos/gonecrzy69/gpstrack/releases" | jq
```

4. Replace an existing asset on a known release:

```bash
API_BASE="${GITEA_URL%/}/api/v1/repos/gonecrzy69/gpstrack"
RELEASE_ID=64
ASSET_ID=91
APK="/root/gpstrack/android/app/build/outputs/apk/debug/app-debug.apk"
NAME="gpstrack-v0.1.0-android-debug.1.apk"

curl -sk -X DELETE \
  -H "Authorization: token $REGISTRY_TOKEN" \
  "$API_BASE/releases/$RELEASE_ID/assets/$ASSET_ID"

curl -sk -X POST \
  -H "Authorization: token $REGISTRY_TOKEN" \
  -F "attachment=@$APK;filename=$NAME" \
  "$API_BASE/releases/$RELEASE_ID/assets"
```

5. Verify the uploaded asset list:

```bash
curl -sk -H "Authorization: token $REGISTRY_TOKEN" \
  "$API_BASE/releases/$RELEASE_ID/assets" | jq
```

If you need a brand new release instead of replacing an asset, create the tag and release first through the Gitea UI or the `/api/v1/repos/{owner}/{repo}/releases` API, then upload the APK asset to that new release id.
