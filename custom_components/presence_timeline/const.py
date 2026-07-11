DOMAIN = "presence_timeline"
INTEGRATION_VERSION = "0.3.1"

PLATFORMS = ("device_tracker", "sensor")

CONF_BASE_URL = "base_url"
CONF_ACCESS_TOKEN = "access_token"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL_SECONDS = 60
API_TIMEOUT_SECONDS = 10

PANEL_FRONTEND_URL_PATH = "presence-timeline"
PANEL_WEB_COMPONENT = "presence-timeline-panel"
PANEL_TITLE = "Presence Timeline"
PANEL_ICON = "mdi:map-marker-path"
PANEL_STATIC_URL = "/api/presence-timeline/static"
PANEL_MODULE_STATIC_URL = f"{PANEL_STATIC_URL}/presence-timeline-panel.js"
PANEL_MODULE_URL = f"{PANEL_MODULE_STATIC_URL}?v={INTEGRATION_VERSION}"
PANEL_STATIC_PATH = "frontend"

PANEL_SUMMARY_API = "/api/presence-timeline/panel/summary"
PANEL_MEMBER_API = "/api/presence-timeline/panel/members/{member_id}"

DATA_COORDINATORS = "__coordinators__"
DATA_PANEL_REGISTERED = "__panel_registered__"
