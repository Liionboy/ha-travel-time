# Travel Time for Home Assistant

A Home Assistant integration that calculates travel time between two locations using multiple routing providers.

## Features

- **Multiple providers**: OpenRouteService (free, 2000 requests/day), Google Maps, or self-hosted OpenRouteService
- **Travel modes**: Driving, Walking, Cycling (Google also supports Transit)
- **Sensors**: Duration, Distance, Arrival Time, Departure Time
- **Traffic data**: Duration in traffic (Google Maps only)
- **Config Flow**: Easy setup through the HA UI — no YAML needed
- **Auto-update**: Configurable refresh interval (default 5 minutes)
- **HACS compatible**: Install directly from HACS

## Providers

### OpenRouteService (Free — Recommended)

1. Sign up at [openrouteservice.org](https://openrouteservice.org/dev/#/signup)
2. Get your free API key (2000 requests/day)
3. Add the integration in HA → Settings → Devices & Services → + Add Integration → Travel Time

### Google Maps

1. Enable the [Directions API](https://console.cloud.google.com/apis/library/directions-backend.googleapis.com) in Google Cloud Console
2. Create an API key
3. Add the integration and select "Google Maps" as provider

### Self-Hosted OpenRouteService

If you run your own [OpenRouteService](https://giscience.github.io/openrouteservice/) instance:

1. Select "OpenRouteService (self-hosted)" as provider
2. Enter your instance URL (e.g., `http://localhost:8080/ors`)
3. Optionally enter an API key if your instance requires one

## Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| **Duration** | Travel time | seconds |
| **Distance** | Travel distance | meters |
| **Arrival Time** | When you'll arrive (if configured) | timestamp |
| **Departure Time** | When you need to leave to arrive on time | timestamp |

## Location Format

Locations are entered as **latitude, longitude** coordinates:

```
44.4268, 26.1025    # Bucharest, Romania
48.8566, 2.3522     # Paris, France
```

You can find coordinates by right-clicking on [Google Maps](https://maps.google.com) or [OpenStreetMap](https://www.openstreetmap.org).

## Example Use Cases

- **Commute time**: Home → Work, updated every 5 minutes
- **School run**: Home → School, with arrival time set to 8:00 AM
- **Airport trip**: Home → Airport, driving mode with traffic (Google)

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

### v1.0.0
- Initial release
- OpenRouteService provider (free + self-hosted)
- Google Maps provider
- Duration, Distance, Arrival Time, Departure Time sensors
- Config Flow setup
- Traffic data support (Google Maps)

---

Made with ❤️ in Romania 🇷🇴
