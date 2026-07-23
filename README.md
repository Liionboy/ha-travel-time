# Travel Time for Home Assistant

A Home Assistant integration that calculates travel time between two locations using multiple routing providers.

## Features

- **Multiple providers**: Waze, OpenRouteService (free, 2000 requests/day), Google Maps, OSRM, or self-hosted OpenRouteService
- **Travel modes**: Driving, Walking, Cycling (Google also supports Transit; Waze supports Car, Taxi, Motorcycle)
- **Sensors**: Duration, Distance, Duration in Traffic, Arrival Time, Departure Time, Origin, Destination, **Alternative Routes**
- **Traffic data**: Real-time traffic (Waze, Google Maps)
- **Alternative routes**: Waze returns multiple route options with comparison data
- **Street names**: Waze provides the list of streets in each route
- **Config Flow**: Easy setup through the HA UI — no YAML needed
- **Auto-update**: Configurable refresh interval (default 5 minutes)
- **HACS compatible**: Install directly from HACS

## Providers

### Waze (Real-Time Traffic — Recommended)

Uses real-time traffic data from Waze. No API key required.

**Features:**
- Real-time traffic-aware ETAs
- Alternative routes with duration/distance comparison
- Street-by-street route names
- Vehicle types: Car, Taxi, Motorcycle
- Avoid options: Toll roads, Subscription roads, Ferries
- Regions: Europe, United States, Israel, Australia
- Time delta: Calculate route as if leaving in X minutes

### OpenRouteService (Free)

1. Sign up at [openrouteservice.org](https://openrouteservice.org/dev/#/signup)
2. Get your free API key (2000 requests/day)
3. Add the integration in HA → Settings → Devices & Services → + Add Integration → Travel Time

### Google Maps

1. Enable the [Directions API](https://console.cloud.google.com/apis/library/directions-backend.googleapis.com) in Google Cloud Console
2. Create an API key
3. Add the integration and select "Google Maps" as provider

### OSRM (Free, No API Key)

Uses the public [OSRM](http://project-osrm.org/) demo server. No registration needed.

**Note:** The demo server may have rate limits and doesn't support traffic data.

### Self-Hosted OpenRouteService

Run your own [OpenRouteService](https://giscience.github.io/openrouteservice/) instance with Docker:

```bash
docker run -d -p 8080:8082 \
  -v ./ors-data:/home/ors \
  -e REBUILD_GRAPHS=True \
  openrouteservice/openrouteservice:v9.9.0
```

Then select "OpenRouteService (self-hosted)" as provider and enter your instance URL (e.g., `http://your-server:8080/ors`).

## Sensors

| Sensor | Description | Unit | Provider |
|--------|-------------|------|----------|
| **Duration** | Travel time | seconds | All |
| **Distance** | Travel distance | meters | All |
| **Duration in Traffic** | Travel time with real-time traffic | seconds | Waze, Google |
| **Origin** | Origin location name | text | All |
| **Destination** | Destination location name | text | All |
| **Arrival Time** | When you'll arrive (if configured) | timestamp | All |
| **Departure Time** | When you need to leave to arrive on time | timestamp | All |
| **Alternative Routes** | Number of alternative routes with details | count | Waze |

### Alternative Routes (Waze)

The **Alternative Routes** sensor provides:
- **State**: Number of alternative routes found
- **Attributes**: List of routes with duration, distance, name, and street names for each

### Street Names (Waze)

The **Duration** sensor includes a `street_names` attribute with the ordered list of streets in the route.

### Duration in Traffic (Waze)

When Waze is used with `realtime=true`, the `duration_in_traffic` attribute equals the real-time traffic-aware duration. This is the same as the main duration for Waze since Waze always includes traffic data.

## Waze Configuration Options

When setting up a Waze route, you get additional options:

| Option | Description | Default |
|--------|-------------|---------|
| **Vehicle Type** | Car, Taxi, or Motorcycle | Car |
| **Region** | Europe, US, Israel, Australia | Europe |
| **Avoid Toll Roads** | Skip toll roads | No |
| **Avoid Subscription Roads** | Skip roads requiring a subscription | No |
| **Avoid Ferries** | Skip ferry routes | No |
| **Time Delta** | Calculate route as if leaving in X minutes (0-120) | 0 |
| **Base Coordinates** | Override Waze map region (advanced) | Auto |

## Location Format

Locations are entered as **latitude, longitude** coordinates:

```
44.4268, 26.1025    # Bucharest, Romania
48.8566, 2.3522     # Paris, France
```

You can find coordinates by right-clicking on [Google Maps](https://maps.google.com) or [OpenStreetMap](https://www.openstreetmap.org).

## Example Use Cases

- **Commute time**: Home → Work, updated every 5 minutes with Waze real-time traffic
- **School run**: Home → School, with arrival time set to 8:00 AM
- **Airport trip**: Home → Airport, with alternative routes to pick the fastest
- **Motorcycle commute**: Waze motorcycle routing with toll road avoidance
- **Future planning**: Time delta of 30 minutes to see traffic conditions when you leave later

## Installation

### Via HACS (Recommended)

1. Open HACS → Integrations
2. Search for "Travel Time"
3. Install and restart Home Assistant
4. Settings → Devices & Services → + Add Integration → Travel Time

### Manual

1. Copy `custom_components/travel_time` to your HA `custom_components/` directory
2. Restart Home Assistant
3. Settings → Devices & Services → + Add Integration → Travel Time

## Changelog

### v1.7.0
- **Waze alternative routes**: New sensor showing multiple route options with comparison
- **Waze street names**: Route streets exposed as attributes
- **Waze vehicle types**: Car, Taxi, Motorcycle support
- **Waze regions**: EU, US, IL, AU configurable
- **Waze avoid options**: Toll roads, Subscription roads, Ferries in config flow UI
- **Waze time delta**: Calculate routes for future departure times
- **Waze base coordinates**: Advanced region override
- New `Alternative Routes` sensor with per-route duration, distance, and street names

### v1.6.3
- Waze provider with real-time traffic
- OSRM provider (free, no API key)
- Reverse geocoding for origin/destination names

### v1.0.0
- Initial release
- OpenRouteService provider (free + self-hosted)
- Google Maps provider
- Duration, Distance, Arrival Time, Departure Time sensors
- Config Flow setup
- Traffic data support (Google Maps)

---

Made with ❤️ in Romania 🇷🇴
