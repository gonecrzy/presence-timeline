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
