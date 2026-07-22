"""Constants for the Travel Time integration."""

DOMAIN = "travel_time"
PLATFORMS = ["sensor"]

# Config entry keys
CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"
CONF_PROVIDER = "provider"
CONF_API_KEY = "api_key"
CONF_BASE_URL = "base_url"
CONF_PROFILE = "profile"
CONF_MODE = "mode"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_ARRIVAL_TIME = "arrival_time"
CONF_DEPARTURE_TIME = "departure_time"
CONF_ROUTE_MODE = "route_mode"
CONF_UNITS = "units"
CONF_NAME = "name"
CONF_ORIGIN_LAT = "origin_lat"
CONF_ORIGIN_LON = "origin_lon"
CONF_DEST_LAT = "dest_lat"
CONF_DEST_LON = "dest_lon"
CONF_ORIGIN_ENTITY_ID = "origin_entity_id"
CONF_DEST_ENTITY_ID = "dest_entity_id"

# Provider values
PROVIDER_ORS = "openrouteservice"
PROVIDER_GOOGLE = "google"
PROVIDER_ORS_SELFHOST = "openrouteservice_selfhost"

# Profile/mode values
PROFILE_DRIVING_CAR = "driving-car"
PROFILE_CYCLING_REGULAR = "cycling-regular"
PROFILE_FOOT_WALKING = "foot-walking"
PROFILE_WHEELCHAIR = "wheelchair"

MODE_DRIVING = "driving"
MODE_WALKING = "walking"
MODE_BICYCLING = "bicycling"
MODE_TRANSIT = "transit"

# Route mode
ROUTE_MODE_FASTEST = "fastest"
ROUTE_MODE_SHORTEST = "shortest"

# Units
UNITS_METRIC = "metric"
UNITS_IMPERIAL = "imperial"

# Defaults
DEFAULT_UPDATE_INTERVAL = 300  # 5 minutes
DEFAULT_NAME = "Travel Time"
DEFAULT_PROFILE = PROFILE_DRIVING_CAR
DEFAULT_MODE = MODE_DRIVING
DEFAULT_ROUTE_MODE = ROUTE_MODE_FASTEST
DEFAULT_UNITS = UNITS_METRIC

# ORS API
ORS_BASE_URL = "https://api.openrouteservice.org"
ORS_DIRECTIONS_PATH = "/v2/directions"

# Google Maps API
GOOGLE_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"

# Attributes
ATTR_DURATION = "duration"
ATTR_DURATION_IN_TRAFFIC = "duration_in_traffic"
ATTR_DISTANCE = "distance"
ATTR_ORIGIN = "origin"
ATTR_DESTINATION = "destination"
ATTR_ARRIVAL_TIME = "arrival_time"
ATTR_DEPARTURE_TIME = "depart_time"
ATTR_ROUTE = "route"
ATTR_ORIGIN_NAME = "origin_name"
ATTR_DESTINATION_NAME = "destination_name"
