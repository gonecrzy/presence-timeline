DOMAIN = "gpstrack"

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
PANEL_MODULE_URL = "/api/gpstrack/static/gpstrack-panel.js"
PANEL_STATIC_PATH = "frontend/gpstrack-panel.js"

PANEL_SUMMARY_API = "/api/gpstrack/panel/summary"
PANEL_MEMBER_API = "/api/gpstrack/panel/members/{member_id}"
