# Home Assistant Roadmap

## Current state

This branch already has real backend value for a Home Assistant-focused product:

- Home Assistant snapshot and websocket ingestion are implemented and tested.
- The database stores normalized location history independently of Home Assistant.
- The service derives trips, stops, daily summaries, safe-zone events, and places.
- The API already exposes the data needed for a dashboard-oriented UI:
  - member list and latest location
  - history and timeline windows
  - stop summaries
  - trips and trip routes
  - daily summaries
  - safety events
  - place CRUD and address search

## What the branch does not have

- A Home Assistant custom integration package
- A Home Assistant config flow for tokens, family selection, and sync options
- Home Assistant entities, sensors, services, or websocket/API adapters
- A dashboard UI inside Home Assistant
- A packaging model for the service in a Home Assistant deployment

## Recommendation

Treat the current FastAPI/PostGIS service as the history engine and build Home Assistant-specific surfaces around it, rather than rewriting the backend into a pure Home Assistant integration first.

That suggests this order:

1. Define the Home Assistant packaging model.
2. Expose a minimal Home Assistant integration surface.
3. Build the first dashboard UI against existing API data.
4. Tighten auth and deployment around the Home Assistant environment.

## Recommended next slices

### Slice 1: Packaging decision

Choose one of these and commit to it before UI work:

- Home Assistant add-on running the existing service plus database dependencies
- Standalone sidecar service with a Home Assistant custom integration

Based on the current code, the sidecar or add-on model is the cleanest fit because this repo already expects a long-running API, a worker, and PostGIS-backed derivation.

### Slice 2: Home Assistant integration shell

Build `custom_components/presence_timeline/` with:

- config entry for service URL and access token
- coordinator to fetch member snapshots and summaries
- basic entities or services for current location and safety status

This creates the first real Home Assistant-native entry point without needing the dashboard to exist yet.

### Slice 3: Dashboard surface

Pick one dashboard path:

- Lovelace cards fed by integration entities for quick adoption
- Custom panel if the trip/history/timeline views need richer map interactions

If history playback and route maps are core, a custom panel is more likely than plain entities plus stock cards.

### Slice 4: Deployment hardening

After the product surface exists:

- replace `open` auth with Home Assistant-aware trust boundaries
- define secrets handling for Home Assistant tokens
- decide whether retention and migrations run inside an add-on lifecycle or an external deploy target

## Immediate code opportunities

If you want to keep moving on this branch, the highest-leverage next implementation is:

1. Scaffold a Home Assistant custom integration shell in `custom_components/presence_timeline/`.
2. Add one integration endpoint in the backend dedicated to dashboard summary data.
3. Wire the integration to expose current member status in Home Assistant.
