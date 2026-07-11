DOMAIN = "gpstrack"
INTEGRATION_VERSION = "0.2.4"

PLATFORMS = ("device_tracker", "sensor")

CONF_BASE_URL = "base_url"
CONF_ACCESS_TOKEN = "access_token"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL_SECONDS = 60
API_TIMEOUT_SECONDS = 10

PANEL_FRONTEND_URL_PATH = "gpstrack"
PANEL_WEB_COMPONENT = "gpstrack-panel"
PANEL_TITLE = "GpsTrack"
PANEL_ICON = "mdi:map-marker-path"
PANEL_MODULE_STATIC_URL = "/api/gpstrack/static/gpstrack-panel.js"
PANEL_MODULE_URL = f"{PANEL_MODULE_STATIC_URL}?v={INTEGRATION_VERSION}"
PANEL_STATIC_PATH = "frontend/gpstrack-panel.js"

PANEL_SUMMARY_API = "/api/gpstrack/panel/summary"
PANEL_MEMBER_API = "/api/gpstrack/panel/members/{member_id}"

DATA_COORDINATORS = "__coordinators__"
DATA_PANEL_REGISTERED = "__panel_registered__"
