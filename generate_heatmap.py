"""
Google Location History Heatmap Generator (Enhanced)

An enhanced fork of the original timeline_google-maps project by Rubens Braz.
Original repository: https://github.com/rubensbraz/timeline_google-maps

Enhancements:
- Interactive time-based filtering (monthly/yearly)
- Animation with smooth transitions
- Custom date range selection
- Playback controls

License: CC BY-NC-SA 4.0 (same as original project)
"""

import ijson
import json
import webbrowser
import os
import re
import traceback

# =============================================================================
# --- GENERAL CONFIGURATION ---
# Adjust the variables in this section to customize the initial state.
# =============================================================================

CONFIG = {
    # --- File Settings ---
    "JSON_INPUT_FILE": "records.json", # Your Google Takeout location history file.
    "HTML_OUTPUT_FILE": "heatmap.html", # The name of the HTML map file to be generated.

    # --- Map Display Settings ---
    "MAP_INITIAL_CENTER": [-15.793889, -47.882778], # Initial map center [Latitude, Longitude].
    "MAP_INITIAL_ZOOM": 4, # Initial map zoom level.
    "MAP_STYLE": "Satellite", # Initial map style. Options: 'OpenStreetMap', 'Dark', 'Light', 'Satellite'

    # --- Heatmap Layer Settings ---
    "HEATMAP_RADIUS": 8,          # Initial radius of influence for each data point, in pixels.
    "HEATMAP_BLUR": 4,             # Initial amount of blur applied to points.
    "HEATMAP_MAX_INTENSITY": 4.0,  # Max intensity for a single point. Lower values make the map "hotter".
    "HEATMAP_MAX_ZOOM": 16,        # The map zoom level at which the heatmap is at its maximum intensity.
    "HEATMAP_MIN_OPACITY": 0.5,    # Initial minimum opacity of the heatmap layer.
    "HEATMAP_GRADIENT": {          # The color gradient of the heatmap.
        0.4: 'blue',
        0.6: 'cyan',
        0.7: 'lime',
        0.8: 'yellow',
        1.0: 'red'
    },

    # --- Data Processing Settings ---
    "INCLUDE_VISITS": True,
    "INCLUDE_ACTIVITIES": True,
    "INCLUDE_RAW_PATH": True,

    # --- Time Filtering Settings ---
    "ENABLE_TIME_FILTER": True,              # Enable time-based filtering and animation controls
    "TIME_GROUPING": "monthly",              # Options: 'monthly', 'yearly'
    "TIME_FILTER_MODE": "static",            # Options: 'static', 'daterange', 'animation'
    "ANIMATION_SPEED": 100,                  # Milliseconds per frame when animating
    "ANIMATION_LOOP": False,                 # Whether to loop animation
    "SMOOTH_TRANSITIONS": True,              # Enable smooth blend transitions between periods
    "INTERPOLATE_MISSING_TIMESTAMPS": True,  # Interpolate timestamps for path points

    # --- Marker Layer Settings ---
    "ENABLE_MARKERS": True,                # Enable clickable location markers with visit statistics
    "MARKERS_VISIBLE_BY_DEFAULT": True,    # Show markers on page load
    "MAX_MARKERS": 5000,                   # Maximum markers to render (performance limit)
    "MARKER_CLUSTER_RADIUS": 50,           # Clustering distance in pixels
    "MARKER_MIN_VISITS": 1,                # Only show locations with N+ visits
    "INCLUDE_PATH_IN_MARKERS": False,      # Whether to include raw path points in markers (not recommended)

    # --- Execution Settings ---
    "AUTO_OPEN_IN_BROWSER": True, # Set to True to automatically open the HTML file after generation.
}

# Dictionary of available map tile URLs.
MAP_STYLE_URLS = {
    "OpenStreetMap": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "Dark": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    "Light": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
}

# Corresponding attribution text for each map style.
MAP_ATTRIBUTIONS = {
    "OpenStreetMap": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
    "Dark": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
    "Light": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
    "Satellite": "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
}

# =============================================================================
# --- SCRIPT LOGIC ---
# It is generally not necessary to modify the code below this line.
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Interactive Location History Heatmap</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    <!-- Marker Clustering Plugin -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <style>
        html, body {
            height: 100%;
            width: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        #map {
            height: 100%;
            width: 100%;
            background-color: #333;
        }
        #controls {
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
            background-color: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(5px);
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 8px;
            padding: 0; /* Padding is now on the inner container */
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            width: 300px;
            transition: all 0.3s ease-in-out;
        }
        #controls-header {
            padding: 10px 15px;
            cursor: pointer;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        #controls-header h3 {
            margin: 0;
            padding: 0;
            font-size: 18px;
            color: #333;
        }
        #toggle-icon {
            font-size: 20px;
            font-weight: bold;
            transition: transform 0.3s;
        }
        #controls-content {
            padding: 15px;
            max-height: 70vh; /* Limit content height */
            overflow-y: auto;
            transition: all 0.3s ease-in-out;
        }
        /* Style for when the panel is collapsed */
        #controls.collapsed #controls-content {
            max-height: 0;
            padding: 0 15px;
            overflow: hidden;
        }
        #controls.collapsed #toggle-icon {
            transform: rotate(-180deg);
        }
        .control-group {
            margin-bottom: 15px;
        }
        .control-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
            font-size: 14px;
        }
        .control-group input[type="range"] {
            width: 100%;
            cursor: pointer;
        }
        .control-group select, .control-group input[type="checkbox"] {
            font-size: 14px;
            width: 100%;
            padding: 5px;
        }
        .control-group .value-display {
            display: inline-block;
            margin-left: 10px;
            font-weight: normal;
            color: #111;
        }

        /* Marker Popup Styling */
        .location-popup {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        .location-popup h4 {
            margin: 0 0 10px 0;
            color: #333;
            font-size: 16px;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 5px;
        }
        .location-popup .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }
        .location-popup .stat-label {
            font-weight: bold;
            color: #666;
        }
        .location-popup .stat-value {
            color: #333;
        }
        .location-popup .coordinates {
            font-size: 11px;
            color: #888;
            margin-top: 10px;
            font-family: monospace;
        }

        /* Custom cluster icons */
        .marker-cluster-small {
            background-color: rgba(181, 226, 140, 0.6);
        }
        .marker-cluster-small div {
            background-color: rgba(110, 204, 57, 0.6);
        }
        .marker-cluster-medium {
            background-color: rgba(241, 211, 87, 0.6);
        }
        .marker-cluster-medium div {
            background-color: rgba(240, 194, 12, 0.6);
        }
        .marker-cluster-large {
            background-color: rgba(253, 156, 115, 0.6);
        }
        .marker-cluster-large div {
            background-color: rgba(241, 128, 23, 0.6);
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="controls">
        <div id="controls-header">
            <h3>Live Controls</h3>
            <span id="toggle-icon">▼</span>
        </div>
        <div id="controls-content">
            <div class="control-group">
                <label for="mapStyle">Map Style</label>
                <select id="mapStyle"></select>
            </div>
            <div class="control-group">
                <label for="radius">Radius <span id="radiusValue" class="value-display"></span></label>
                <input type="range" id="radius" min="1" max="50" step="1">
            </div>
            <div class="control-group">
                <label for="blur">Blur <span id="blurValue" class="value-display"></span></label>
                <input type="range" id="blur" min="1" max="50" step="1">
            </div>
            <div class="control-group">
                <label for="maxIntensity">Max Intensity <span id="maxIntensityValue" class="value-display"></span></label>
                <input type="range" id="maxIntensity" min="0.1" max="10" step="0.1">
            </div>
            <div class="control-group">
                <label for="maxZoom">Heatmap Max Zoom <span id="maxZoomValue" class="value-display"></span></label>
                <input type="range" id="maxZoom" min="1" max="18" step="1">
            </div>

            <!-- Marker Layer Controls -->
            <div class="control-group" id="markerToggleControl">
                <label style="display: flex; align-items: center; gap: 5px;">
                    <input type="checkbox" id="showMarkersToggle" style="width: auto;" checked>
                    <span>Show Location Markers</span>
                </label>
                <div id="markerStats" style="font-size: 12px; color: #666; margin-top: 5px;">
                    <!-- Populated dynamically with marker counts -->
                </div>
            </div>

            <!-- Time Filtering Controls -->
            <div class="control-group" id="timeFilterModeControl">
                <label for="timeFilterMode">Time Filter Mode</label>
                <select id="timeFilterMode">
                    <option value="static">Static (All Data)</option>
                    <option value="daterange">Date Range</option>
                    <option value="animation">Animation</option>
                </select>
            </div>

            <div class="control-group" id="timeGroupingControl" style="display: none;">
                <label for="timeGrouping">Time Grouping</label>
                <select id="timeGrouping">
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                </select>
            </div>

            <div class="control-group" id="dateRangeControl" style="display: none;">
                <label>Date Range</label>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-bottom: 5px;">
                    <select id="startMonth" style="width: 100%; padding: 5px;"></select>
                    <select id="startYear" style="width: 100%; padding: 5px;"></select>
                </div>
                <div style="text-align: center; margin: 5px 0; font-size: 12px; color: #666;">to</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px;">
                    <select id="endMonth" style="width: 100%; padding: 5px;"></select>
                    <select id="endYear" style="width: 100%; padding: 5px;"></select>
                </div>
                <button id="applyDateRange" style="width: 100%; margin-top: 10px; padding: 8px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">Set Range</button>
            </div>

            <div class="control-group" id="timeSliderControl" style="display: none;">
                <label>Timeline <span id="currentPeriod" class="value-display"></span></label>
                <input type="range" id="timeSlider" min="0" max="100" step="1" value="0">
                <div id="pointCount" class="value-display" style="margin-top: 5px;"></div>
                <div id="sliderHint" style="font-size: 11px; color: #888; margin-top: 5px; font-style: italic;"></div>
            </div>

            <div class="control-group" id="animationControls" style="display: none;">
                <div style="display: flex; gap: 5px; margin-bottom: 10px;">
                    <button id="stepBack" style="flex: 1;">⏮️</button>
                    <button id="playPause" style="flex: 2;">▶️ Play</button>
                    <button id="stepForward" style="flex: 1;">⏭️</button>
                </div>
                <label style="display: flex; align-items: center; gap: 5px;">
                    <input type="checkbox" id="loopAnimation" style="width: auto;">
                    <span>Loop Animation</span>
                </label>
                <label for="animationSpeed">Speed <span id="animationSpeedValue" class="value-display"></span>ms</label>
                <input type="range" id="animationSpeed" min="100" max="5000" step="100" value="1000">
                <label style="display: flex; align-items: center; gap: 5px; margin-top: 10px;">
                    <input type="checkbox" id="smoothAnimation" style="width: auto;" checked>
                    <span>Smooth Transitions</span>
                </label>
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    <script>
        // --- Data and Configuration Injected by Python ---
        const locationData = %(LOCATIONS_DATA)s;
        const initialHeatOptions = %(HEATMAP_OPTIONS)s;
        const timeConfig = %(TIME_CONFIG)s;
        const markerConfig = %(MARKER_CONFIG)s;
        const mapCenter = %(MAP_CENTER)s;
        const mapZoom = %(MAP_ZOOM)s;
        const initialMapStyle = '%(INITIAL_MAP_STYLE)s';
        const mapStyles = %(MAP_STYLES_JS)s;
        const mapAttributions = %(MAP_ATTRIBUTIONS_JS)s;

        // --- Map Initialization ---
        const map = L.map('map').setView(mapCenter, mapZoom);
        let tileLayer = L.tileLayer(mapStyles[initialMapStyle], {
            attribution: mapAttributions[initialMapStyle],
            maxZoom: 19
        }).addTo(map);

        // Transform location data for heatmap (extract [lat, lon])
        const heatmapData = locationData.map(p => [p.lat, p.lon]);
        const heatLayer = L.heatLayer(heatmapData, initialHeatOptions).addTo(map);

        // --- Marker Layer Logic ---
        let markerClusterGroup = null;
        let markersEnabled = markerConfig.visibleByDefault;
        const spatialIndex = new Map(); // key: "lat,lon" -> array of point objects

        function buildSpatialIndex(data) {
            spatialIndex.clear();
            data.forEach(point => {
                // Skip raw path points for markers unless configured to include them
                if (point.source === 'path' && !markerConfig.includePathInMarkers) return;

                // Round to 4 decimal places (~11 meters precision)
                const gridKey = `${point.lat.toFixed(4)},${point.lon.toFixed(4)}`;

                if (!spatialIndex.has(gridKey)) {
                    spatialIndex.set(gridKey, []);
                }
                spatialIndex.get(gridKey).push(point);
            });
        }

        function calculateVisitStats(points) {
            const totalVisits = points.length;

            // Extract unique dates (YYYY-MM-DD format)
            const uniqueDates = new Set();
            points.forEach(p => {
                if (p.timestamp) {
                    const date = new Date(p.timestamp);
                    const dateKey = `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
                    uniqueDates.add(dateKey);
                }
            });

            // Calculate consecutive day streaks
            const sortedDates = Array.from(uniqueDates).sort();
            let maxStreak = 0;
            let currentStreak = 0;
            let prevDate = null;

            sortedDates.forEach(dateStr => {
                const currentDate = new Date(dateStr);

                if (prevDate) {
                    const dayDiff = Math.round((currentDate - prevDate) / (1000 * 60 * 60 * 24));
                    if (dayDiff === 1) {
                        currentStreak++;
                    } else {
                        maxStreak = Math.max(maxStreak, currentStreak);
                        currentStreak = 1;
                    }
                } else {
                    currentStreak = 1;
                }

                prevDate = currentDate;
            });
            maxStreak = Math.max(maxStreak, currentStreak);

            // Get semantic type (prioritize most confident visit)
            let bestSemanticType = 'Unknown Location';
            let highestProb = 0;
            points.forEach(p => {
                if (p.semanticType && p.probability > highestProb) {
                    bestSemanticType = p.semanticType;
                    highestProb = p.probability;
                }
            });

            // Fallback: if no semantic type found, use the first non-null one
            if (bestSemanticType === 'Unknown Location') {
                for (let p of points) {
                    if (p.semanticType) {
                        bestSemanticType = p.semanticType;
                        break;
                    }
                }
            }

            // Get first and last visit dates
            const timestamps = points.map(p => p.timestamp).filter(t => t).sort((a, b) => a - b);
            const firstVisit = timestamps.length > 0 ? new Date(timestamps[0]).toLocaleDateString() : 'Unknown';
            const lastVisit = timestamps.length > 0 ? new Date(timestamps[timestamps.length - 1]).toLocaleDateString() : 'Unknown';

            return {
                totalVisits,
                uniqueDays: uniqueDates.size,
                maxConsecutiveDays: maxStreak,
                semanticType: bestSemanticType,
                firstVisit,
                lastVisit,
                avgLat: points.reduce((sum, p) => sum + p.lat, 0) / points.length,
                avgLon: points.reduce((sum, p) => sum + p.lon, 0) / points.length
            };
        }

        function createPopupContent(stats) {
            return `
                <div class="location-popup">
                    <h4>${stats.semanticType}</h4>
                    <div class="stat-row">
                        <span class="stat-label">Total Visits:</span>
                        <span class="stat-value">${stats.totalVisits}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Unique Days:</span>
                        <span class="stat-value">${stats.uniqueDays}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Longest Streak:</span>
                        <span class="stat-value">${stats.maxConsecutiveDays} day${stats.maxConsecutiveDays !== 1 ? 's' : ''}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">First Visit:</span>
                        <span class="stat-value">${stats.firstVisit}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Last Visit:</span>
                        <span class="stat-value">${stats.lastVisit}</span>
                    </div>
                    <div class="coordinates">
                        ${stats.avgLat.toFixed(6)}, ${stats.avgLon.toFixed(6)}
                    </div>
                </div>
            `;
        }

        function createMarkerLayer(data) {
            // Remove existing marker layer if present
            if (markerClusterGroup) {
                map.removeLayer(markerClusterGroup);
            }

            // Build spatial index from data
            buildSpatialIndex(data);

            // Create new cluster group
            markerClusterGroup = L.markerClusterGroup({
                maxClusterRadius: markerConfig.clusterRadius,
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: false,
                zoomToBoundsOnClick: false,  // We'll handle clicks manually for aggregation
                iconCreateFunction: function(cluster) {
                    const count = cluster.getChildCount();
                    let className = 'marker-cluster-';
                    if (count < 10) {
                        className += 'small';
                    } else if (count < 100) {
                        className += 'medium';
                    } else {
                        className += 'large';
                    }

                    return L.divIcon({
                        html: '<div><span>' + count + '</span></div>',
                        className: 'marker-cluster ' + className,
                        iconSize: L.point(40, 40)
                    });
                }
            });

            // Apply marker limit for performance
            let entriesToProcess = Array.from(spatialIndex.entries());
            if (entriesToProcess.length > markerConfig.maxMarkers) {
                // Sample evenly to stay under limit
                const step = Math.ceil(entriesToProcess.length / markerConfig.maxMarkers);
                entriesToProcess = entriesToProcess.filter((_, index) => index % step === 0);
            }

            // Create markers from spatial index
            entriesToProcess.forEach(([gridKey, points]) => {
                if (points.length < markerConfig.minVisits) return;

                const stats = calculateVisitStats(points);

                // Create marker at average position
                const marker = L.marker([stats.avgLat, stats.avgLon], {
                    icon: L.divIcon({
                        className: 'custom-marker',
                        html: `<div style="background-color: #4CAF50; border-radius: 50%; width: 10px; height: 10px; border: 2px solid white;"></div>`,
                        iconSize: [10, 10]
                    })
                });

                // Bind popup
                marker.bindPopup(createPopupContent(stats), {
                    maxWidth: 300,
                    closeButton: true
                });

                markerClusterGroup.addLayer(marker);
            });

            // Handle cluster clicks for aggregation
            markerClusterGroup.on('clusterclick', function(event) {
                const cluster = event.layer;
                const childMarkers = cluster.getAllChildMarkers();

                // Limit aggregation for performance
                if (childMarkers.length > 500) {
                    // Just zoom in instead of aggregating
                    cluster.zoomToBounds();
                    return;
                }

                // Aggregate all points from all markers in cluster
                let allPoints = [];
                childMarkers.forEach(marker => {
                    const latLng = marker.getLatLng();
                    const gridKey = `${latLng.lat.toFixed(4)},${latLng.lng.toFixed(4)}`;
                    if (spatialIndex.has(gridKey)) {
                        allPoints = allPoints.concat(spatialIndex.get(gridKey));
                    }
                });

                const aggregateStats = calculateVisitStats(allPoints);
                aggregateStats.semanticType = `${childMarkers.length} Locations`;

                // Show popup at cluster position
                L.popup()
                    .setLatLng(cluster.getLatLng())
                    .setContent(createPopupContent(aggregateStats))
                    .openOn(map);
            });

            // Add to map if enabled
            if (markersEnabled) {
                map.addLayer(markerClusterGroup);
                // Ensure heatmap stays behind markers
                heatLayer.bringToBack();
            }

            // Update stats display
            updateMarkerStats();
        }

        function updateMarkerStats() {
            const statsDiv = document.getElementById('markerStats');
            if (markerClusterGroup) {
                const markerCount = markerClusterGroup.getLayers().length;
                const locationCount = spatialIndex.size;
                statsDiv.textContent = `${markerCount} markers representing ${locationCount} unique locations`;
            }
        }

        // --- Controls Logic ---
        const controls = document.getElementById('controls');
        const controlsHeader = document.getElementById('controls-header');
        const radiusSlider = document.getElementById('radius');
        const blurSlider = document.getElementById('blur');
        const maxIntensitySlider = document.getElementById('maxIntensity');
        const maxZoomSlider = document.getElementById('maxZoom');
        const radiusValue = document.getElementById('radiusValue');
        const blurValue = document.getElementById('blurValue');
        const maxIntensityValue = document.getElementById('maxIntensityValue');
        const maxZoomValue = document.getElementById('maxZoomValue');
        const mapStyleSelect = document.getElementById('mapStyle');

        // Function to set initial values for controls from config
        function setInitialControlValues() {
            radiusSlider.value = initialHeatOptions.radius;
            blurSlider.value = initialHeatOptions.blur;
            maxIntensitySlider.value = initialHeatOptions.max;
            maxZoomSlider.value = initialHeatOptions.maxZoom;
            
            radiusValue.textContent = radiusSlider.value;
            blurValue.textContent = blurSlider.value;
            maxIntensityValue.textContent = maxIntensitySlider.value;
            maxZoomValue.textContent = maxZoomSlider.value;
        }

        // --- Event Listeners ---
        controlsHeader.addEventListener('click', () => {
            controls.classList.toggle('collapsed');
        });

        const updateHeatmapOptions = () => {
            heatLayer.setOptions({
                radius: parseInt(radiusSlider.value, 10),
                blur: parseInt(blurSlider.value, 10),
                max: parseFloat(maxIntensitySlider.value),
                maxZoom: parseInt(maxZoomSlider.value, 10),
            });
        };
        
        radiusSlider.addEventListener('input', e => {
            radiusValue.textContent = e.target.value;
            updateHeatmapOptions();
        });
        blurSlider.addEventListener('input', e => {
            blurValue.textContent = e.target.value;
            updateHeatmapOptions();
        });
        maxIntensitySlider.addEventListener('input', e => {
            maxIntensityValue.textContent = e.target.value;
            updateHeatmapOptions();
        });
        maxZoomSlider.addEventListener('input', e => {
            maxZoomValue.textContent = e.target.value;
            updateHeatmapOptions();
        });

        mapStyleSelect.addEventListener('change', e => {
            const newStyle = e.target.value;
            tileLayer.setUrl(mapStyles[newStyle]);
            map.attributionControl.setPrefix(mapAttributions[newStyle]);
        });

        // --- Time Filtering Logic ---
        let timeFilteredData = locationData;
        let timePeriods = [];
        let currentPeriodIndex = 0;
        let animationInterval = null;
        let isTransitioning = false;
        let previousPeriodPoints = [];
        let filteredDataForRange = []; // All data in the current date range
        let showingFullRange = true; // Whether we're showing all data in range or drilling down

        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

        const timeFilterModeSelect = document.getElementById('timeFilterMode');
        const timeGroupingSelect = document.getElementById('timeGrouping');
        const timeSlider = document.getElementById('timeSlider');
        const currentPeriodSpan = document.getElementById('currentPeriod');
        const pointCountDiv = document.getElementById('pointCount');
        const playPauseButton = document.getElementById('playPause');
        const stepBackButton = document.getElementById('stepBack');
        const stepForwardButton = document.getElementById('stepForward');
        const loopCheckbox = document.getElementById('loopAnimation');
        const animationSpeedSlider = document.getElementById('animationSpeed');
        const animationSpeedValue = document.getElementById('animationSpeedValue');
        const smoothAnimationCheckbox = document.getElementById('smoothAnimation');

        // Date range controls
        const startMonthSelect = document.getElementById('startMonth');
        const startYearSelect = document.getElementById('startYear');
        const endMonthSelect = document.getElementById('endMonth');
        const endYearSelect = document.getElementById('endYear');
        const applyDateRangeButton = document.getElementById('applyDateRange');
        const sliderHint = document.getElementById('sliderHint');

        function formatPeriod(timestamp, grouping) {
            if (!timestamp) return 'No Date';
            const date = new Date(timestamp);
            if (grouping === 'yearly') {
                return date.getFullYear().toString();
            } else {
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const year = String(date.getFullYear()).slice(2);
                return `${month}/${year}`;
            }
        }

        function getPeriodKey(timestamp, grouping) {
            if (!timestamp) return null;
            const date = new Date(timestamp);
            if (grouping === 'yearly') {
                return date.getFullYear();
            } else {
                return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            }
        }

        function groupDataByTimePeriod(data, grouping) {
            const groups = new Map();

            data.forEach(point => {
                if (!point.timestamp) return; // Skip points without timestamps

                const periodKey = getPeriodKey(point.timestamp, grouping);
                if (!periodKey) return;

                if (!groups.has(periodKey)) {
                    groups.set(periodKey, {
                        key: periodKey,
                        timestamp: point.timestamp,
                        points: [],  // For heatmap (just [lat, lon])
                        fullData: []  // For markers (full point objects)
                    });
                }
                groups.get(periodKey).points.push([point.lat, point.lon]);
                groups.get(periodKey).fullData.push(point);
            });

            // Convert to sorted array
            const periods = Array.from(groups.values()).sort((a, b) => a.timestamp - b.timestamp);
            return periods;
        }

        function updateTimePeriods() {
            const grouping = timeGroupingSelect.value;
            timePeriods = groupDataByTimePeriod(locationData, grouping);

            if (timePeriods.length > 0) {
                timeSlider.max = timePeriods.length - 1;
                timeSlider.value = Math.min(currentPeriodIndex, timePeriods.length - 1);
                currentPeriodIndex = parseInt(timeSlider.value);
                updateHeatmapForCurrentPeriod();
            }
        }

        function updateHeatmapForCurrentPeriod() {
            const mode = timeFilterModeSelect.value;

            if (mode === 'static' || timePeriods.length === 0) {
                // Show all data
                setHeatmapData(locationData.map(p => [p.lat, p.lon]), 'All Time', locationData.length);
                // Update markers with all data
                if (markerConfig.enabled) {
                    try {
                        createMarkerLayer(locationData);
                    } catch (error) {
                        console.error('Error updating markers:', error);
                    }
                }
            } else if (mode === 'daterange' && showingFullRange) {
                // Date Range mode: show ALL data in the selected range
                const points = filteredDataForRange.map(p => [p.lat, p.lon]);
                const startMonth = parseInt(startMonthSelect.value);
                const startYear = parseInt(startYearSelect.value);
                const endMonth = parseInt(endMonthSelect.value);
                const endYear = parseInt(endYearSelect.value);
                const label = `${monthNames[startMonth]} ${startYear} - ${monthNames[endMonth]} ${endYear}`;
                setHeatmapData(points, label, filteredDataForRange.length);
                // Update markers with filtered range data
                if (markerConfig.enabled) {
                    try {
                        createMarkerLayer(filteredDataForRange);
                    } catch (error) {
                        console.error('Error updating markers:', error);
                    }
                }
            } else {
                // Animation mode OR Date Range mode with slider drill-down: show data for current period
                const period = timePeriods[currentPeriodIndex];
                if (period) {
                    const label = formatPeriod(period.timestamp, timeGroupingSelect.value);
                    setHeatmapData(period.points, label, period.points.length);
                    // Update markers with period data
                    if (markerConfig.enabled) {
                        try {
                            createMarkerLayer(period.fullData);
                        } catch (error) {
                            console.error('Error updating markers:', error);
                        }
                    }
                }
            }
        }

        function setHeatmapData(points, label, count) {
            const shouldSmooth = smoothAnimationCheckbox && smoothAnimationCheckbox.checked;

            if (shouldSmooth && !isTransitioning && previousPeriodPoints.length > 0) {
                // Smooth transition by blending old and new data over multiple frames
                isTransitioning = true;
                const blendFrames = 8; // Number of intermediate frames
                const frameDuration = 30; // ms per frame
                let currentFrame = 0;

                const blendInterval = setInterval(() => {
                    currentFrame++;
                    const progress = currentFrame / blendFrames;

                    // Blend between old and new data
                    const blendedPoints = blendDataPoints(previousPeriodPoints, points, progress);
                    heatLayer.setLatLngs(blendedPoints);

                    if (currentFrame >= blendFrames) {
                        clearInterval(blendInterval);
                        // Final update with exact new data
                        heatLayer.setLatLngs(points);
                        previousPeriodPoints = [...points];
                        isTransitioning = false;
                    }
                }, frameDuration);

                // Update labels immediately
                currentPeriodSpan.textContent = label;
                pointCountDiv.textContent = `${count.toLocaleString()} points`;
            } else {
                // Instant update
                heatLayer.setLatLngs(points);
                currentPeriodSpan.textContent = label;
                pointCountDiv.textContent = `${count.toLocaleString()} points`;
                previousPeriodPoints = [...points];
            }
        }

        function blendDataPoints(oldPoints, newPoints, progress) {
            // Progress: 0 = all old data, 1 = all new data
            // We'll create a blend by mixing samples from both datasets

            const oldSampleSize = Math.floor(oldPoints.length * (1 - progress));
            const newSampleSize = Math.floor(newPoints.length * progress);

            const blended = [];

            // Sample from old data (with decreasing weight)
            for (let i = 0; i < oldSampleSize; i++) {
                const index = Math.floor((i / oldSampleSize) * oldPoints.length);
                if (index < oldPoints.length) {
                    blended.push(oldPoints[index]);
                }
            }

            // Sample from new data (with increasing weight)
            for (let i = 0; i < newSampleSize; i++) {
                const index = Math.floor((i / newSampleSize) * newPoints.length);
                if (index < newPoints.length) {
                    blended.push(newPoints[index]);
                }
            }

            return blended;
        }

        function populateDateRangeSelectors() {
            // Get min and max dates from data
            let minTimestamp = Infinity;
            let maxTimestamp = -Infinity;

            locationData.forEach(point => {
                if (point.timestamp) {
                    minTimestamp = Math.min(minTimestamp, point.timestamp);
                    maxTimestamp = Math.max(maxTimestamp, point.timestamp);
                }
            });

            if (minTimestamp === Infinity || maxTimestamp === -Infinity) {
                return; // No valid timestamps
            }

            const minDate = new Date(minTimestamp);
            const maxDate = new Date(maxTimestamp);
            const minYear = minDate.getFullYear();
            const maxYear = maxDate.getFullYear();

            // Populate month selectors
            monthNames.forEach((month, index) => {
                const option1 = document.createElement('option');
                option1.value = index;
                option1.textContent = month;
                startMonthSelect.appendChild(option1);

                const option2 = document.createElement('option');
                option2.value = index;
                option2.textContent = month;
                endMonthSelect.appendChild(option2);
            });

            // Populate year selectors
            for (let year = minYear; year <= maxYear; year++) {
                const option1 = document.createElement('option');
                option1.value = year;
                option1.textContent = year;
                startYearSelect.appendChild(option1);

                const option2 = document.createElement('option');
                option2.value = year;
                option2.textContent = year;
                endYearSelect.appendChild(option2);
            }

            // Set defaults to full range
            startMonthSelect.value = minDate.getMonth();
            startYearSelect.value = minYear;
            endMonthSelect.value = maxDate.getMonth();
            endYearSelect.value = maxYear;
        }

        function applyCustomDateRange() {
            stopAnimation(); // Stop any running animation

            const startMonth = parseInt(startMonthSelect.value);
            const startYear = parseInt(startYearSelect.value);
            const endMonth = parseInt(endMonthSelect.value);
            const endYear = parseInt(endYearSelect.value);

            const startDate = new Date(startYear, startMonth, 1);
            const endDate = new Date(endYear, endMonth + 1, 0, 23, 59, 59, 999); // Last day of end month

            // Validate date range
            if (startDate > endDate) {
                alert('Start date must be before end date');
                return;
            }

            // Filter data by date range
            const filteredData = locationData.filter(point => {
                if (!point.timestamp) return false;
                const pointDate = new Date(point.timestamp);
                return pointDate >= startDate && pointDate <= endDate;
            });

            if (filteredData.length === 0) {
                alert('No data found in selected date range');
                return;
            }

            // Store filtered data for the full range view
            filteredDataForRange = filteredData;

            // Regroup filtered data for slider drill-down
            const grouping = timeGroupingSelect.value;
            timePeriods = groupDataByTimePeriod(filteredData, grouping);

            if (timePeriods.length > 0) {
                // Reset to showing full range
                showingFullRange = true;
                timeSlider.max = timePeriods.length - 1;
                currentPeriodIndex = 0;
                timeSlider.value = 0;

                // Update the display to show ALL data in range
                updateHeatmapForCurrentPeriod();

                // Show hint for Date Range mode
                if (timeFilterModeSelect.value === 'daterange') {
                    sliderHint.textContent = 'Use slider to drill down into individual periods';
                }

                // Show feedback
                console.log(`Date range applied: ${monthNames[startMonth]} ${startYear} - ${monthNames[endMonth]} ${endYear}`);
                console.log(`Showing ${filteredData.length} total points across ${timePeriods.length} time periods`);
            }
        }

        function startAnimation() {
            if (animationInterval) return; // Already playing

            const speed = parseInt(animationSpeedSlider.value);
            animationInterval = setInterval(() => {
                currentPeriodIndex++;

                if (currentPeriodIndex >= timePeriods.length) {
                    if (loopCheckbox.checked) {
                        currentPeriodIndex = 0;
                    } else {
                        stopAnimation();
                        currentPeriodIndex = timePeriods.length - 1;
                        return;
                    }
                }

                timeSlider.value = currentPeriodIndex;
                updateHeatmapForCurrentPeriod();
            }, speed);

            playPauseButton.textContent = '⏸️ Pause';
        }

        function stopAnimation() {
            if (animationInterval) {
                clearInterval(animationInterval);
                animationInterval = null;
                playPauseButton.textContent = '▶️ Play';
            }
        }

        function toggleControlsVisibility() {
            const mode = timeFilterModeSelect.value;
            const timeGroupingControl = document.getElementById('timeGroupingControl');
            const dateRangeControl = document.getElementById('dateRangeControl');
            const timeSliderControl = document.getElementById('timeSliderControl');
            const animationControlsDiv = document.getElementById('animationControls');

            if (!timeConfig.enabled) {
                document.getElementById('timeFilterModeControl').style.display = 'none';
                return;
            }

            // Clear slider hint when changing modes
            sliderHint.textContent = '';

            if (mode === 'static') {
                timeGroupingControl.style.display = 'none';
                dateRangeControl.style.display = 'none';
                timeSliderControl.style.display = 'none';
                animationControlsDiv.style.display = 'none';
            } else if (mode === 'daterange') {
                timeGroupingControl.style.display = 'block';
                dateRangeControl.style.display = 'block';
                timeSliderControl.style.display = 'block';
                animationControlsDiv.style.display = 'none';
            } else if (mode === 'animation') {
                timeGroupingControl.style.display = 'block';
                dateRangeControl.style.display = 'block';
                timeSliderControl.style.display = 'block';
                animationControlsDiv.style.display = 'block';
                sliderHint.textContent = '';
            }
        }

        // --- Time Filter Event Listeners ---
        if (timeConfig.enabled) {
            timeFilterModeSelect.value = timeConfig.mode;
            timeGroupingSelect.value = timeConfig.grouping;
            animationSpeedSlider.value = timeConfig.animationSpeed;
            loopCheckbox.checked = timeConfig.animationLoop;
            smoothAnimationCheckbox.checked = timeConfig.smoothTransitions;
            animationSpeedValue.textContent = timeConfig.animationSpeed;

            timeFilterModeSelect.addEventListener('change', () => {
                stopAnimation();
                toggleControlsVisibility();
                if (timeFilterModeSelect.value !== 'static') {
                    updateTimePeriods();
                } else {
                    updateHeatmapForCurrentPeriod();
                }
            });

            timeGroupingSelect.addEventListener('change', () => {
                stopAnimation();
                currentPeriodIndex = 0;
                updateTimePeriods();
            });

            timeSlider.addEventListener('input', (e) => {
                stopAnimation();
                currentPeriodIndex = parseInt(e.target.value);
                // When user moves the slider in daterange mode, switch to drill-down mode
                if (timeFilterModeSelect.value === 'daterange') {
                    showingFullRange = false;
                    sliderHint.textContent = ''; // Clear hint when drilling down
                }
                updateHeatmapForCurrentPeriod();
            });

            playPauseButton.addEventListener('click', () => {
                if (animationInterval) {
                    stopAnimation();
                } else {
                    startAnimation();
                }
            });

            stepBackButton.addEventListener('click', () => {
                stopAnimation();
                currentPeriodIndex = Math.max(0, currentPeriodIndex - 1);
                timeSlider.value = currentPeriodIndex;
                updateHeatmapForCurrentPeriod();
            });

            stepForwardButton.addEventListener('click', () => {
                stopAnimation();
                currentPeriodIndex = Math.min(timePeriods.length - 1, currentPeriodIndex + 1);
                timeSlider.value = currentPeriodIndex;
                updateHeatmapForCurrentPeriod();
            });

            animationSpeedSlider.addEventListener('input', (e) => {
                animationSpeedValue.textContent = e.target.value;
                if (animationInterval) {
                    stopAnimation();
                    startAnimation();
                }
            });

            applyDateRangeButton.addEventListener('click', () => {
                applyCustomDateRange();
            });

            // Initialize time filtering
            populateDateRangeSelectors();
            toggleControlsVisibility();
            if (timeConfig.mode !== 'static') {
                updateTimePeriods();
            } else {
                updateHeatmapForCurrentPeriod();
            }
        }

        // --- Marker Toggle Event Listener ---
        if (markerConfig.enabled) {
            document.getElementById('showMarkersToggle').addEventListener('change', (e) => {
                markersEnabled = e.target.checked;
                if (markersEnabled) {
                    if (markerClusterGroup) {
                        map.addLayer(markerClusterGroup);
                        heatLayer.bringToBack();
                    }
                } else {
                    if (markerClusterGroup) {
                        map.removeLayer(markerClusterGroup);
                    }
                }
            });
        }

        // --- Initialization ---
        Object.keys(mapStyles).forEach(styleName => {
            const option = document.createElement('option');
            option.value = styleName;
            option.textContent = styleName;
            mapStyleSelect.appendChild(option);
        });
        mapStyleSelect.value = initialMapStyle;
        setInitialControlValues();

        // --- Initialize Marker Layer (after controls are set up) ---
        if (markerConfig.enabled) {
            try {
                createMarkerLayer(locationData);
            } catch (error) {
                console.error('Error initializing marker layer:', error);
                // Hide marker control if initialization fails
                document.getElementById('markerToggleControl').style.display = 'none';
            }
        } else {
            // Hide the marker toggle control if markers are disabled
            document.getElementById('markerToggleControl').style.display = 'none';
        }
    </script>
</body>
</html>
"""

def _parse_timestamp(timestamp_data):
    """
    Parse timestamp from various Google Takeout formats.
    Returns Unix epoch milliseconds (JavaScript-compatible) or None.

    Handles:
    - timestampMs (string): "1609459200000"
    - timestamp (string): ISO 8601 format "2021-01-01T00:00:00Z"
    - Various other timestamp objects and formats
    """
    from datetime import datetime

    if not timestamp_data:
        return None

    try:
        # If it's already a number (milliseconds)
        if isinstance(timestamp_data, (int, float)):
            return int(timestamp_data)

        # If it's a string that looks like epoch milliseconds
        if isinstance(timestamp_data, str):
            # Try parsing as milliseconds epoch
            if timestamp_data.isdigit():
                return int(timestamp_data)

            # Try parsing ISO 8601 format
            try:
                # Handle various ISO formats
                dt = datetime.fromisoformat(timestamp_data.replace('Z', '+00:00'))
                return int(dt.timestamp() * 1000)
            except:
                pass

        # If it's a dict with timestamp fields
        if isinstance(timestamp_data, dict):
            if 'timestampMs' in timestamp_data:
                return int(timestamp_data['timestampMs'])
            if 'timestamp' in timestamp_data:
                return _parse_timestamp(timestamp_data['timestamp'])

        return None
    except:
        return None

def _process_locations_format(file_handle):
    """Processes the older 'locations' array format from Google Takeout or iOS."""
    print("[INFO] 'locations' format detected. Processing...")
    points = []
    # Google stores coordinates as integers, so they must be scaled by 1e-7.
    E7 = 1e-7
    locations = ijson.items(file_handle, 'locations.item')
    for i, loc in enumerate(locations):
        if 'latitudeE7' in loc and 'longitudeE7' in loc:
            lat = loc['latitudeE7'] * E7
            lon = loc['longitudeE7'] * E7
            # Extract timestamp
            timestamp = _parse_timestamp(loc.get('timestampMs') or loc.get('timestamp'))
            # Old format doesn't have semantic metadata
            points.append({
                'lat': lat,
                'lon': lon,
                'timestamp': timestamp,
                'placeID': None,
                'semanticType': 'Location',  # Generic label for old format
                'probability': 0.0,
                'source': 'path'  # Old format is raw location data
            })
        if (i + 1) % 50000 == 0:
            print(f"  [PROGRESS] {i+1:,} locations processed...")
    return points

def _process_semantic_segments_format(file_handle, config):
    """Processes the newer 'semanticSegments' (Android) format."""
    print("[INFO] 'semanticSegments' format detected. Processing...")
    points = []
    # Regular expression to find floating-point numbers in coordinate strings.
    coord_regex = re.compile(r"([-]?\d+\.\d+)")
    def parse_lat_lng_string(lat_lng_str):
        if not isinstance(lat_lng_str, str): return None
        try:
            coords = [float(c) for c in coord_regex.findall(lat_lng_str)]
            return [coords[0], coords[1]] if len(coords) == 2 else None
        except (ValueError, AttributeError): return None

    segments = ijson.items(file_handle, 'semanticSegments.item')
    for i, segment in enumerate(segments):
        try:
            if config["INCLUDE_RAW_PATH"] and 'timelinePath' in segment:
                timeline_path = segment.get('timelinePath', [])
                # Get segment start/end times for interpolation
                start_time = _parse_timestamp(segment.get('startTime'))
                end_time = _parse_timestamp(segment.get('endTime'))

                for idx, path_point in enumerate(timeline_path):
                    if coords := parse_lat_lng_string(path_point.get('point')):
                        # Try to get point-specific timestamp, or interpolate
                        point_time = _parse_timestamp(path_point.get('time') or path_point.get('timestamp'))
                        if not point_time and config["INTERPOLATE_MISSING_TIMESTAMPS"] and start_time and end_time:
                            # Interpolate timestamp based on position in path
                            progress = idx / max(len(timeline_path) - 1, 1)
                            point_time = int(start_time + (end_time - start_time) * progress)
                        points.append({
                            'lat': coords[0],
                            'lon': coords[1],
                            'timestamp': point_time,
                            'placeID': None,
                            'semanticType': None,
                            'probability': 0.0,
                            'source': 'path'
                        })

            elif config["INCLUDE_VISITS"] and 'visit' in segment:
                if lat_lng := segment.get('visit', {}).get('topCandidate', {}).get('placeLocation', {}).get('latLng'):
                    if coords := parse_lat_lng_string(lat_lng):
                        # Use visit start time or duration start time
                        visit_data = segment.get('visit', {})
                        top_candidate = visit_data.get('topCandidate', {})
                        timestamp = _parse_timestamp(
                            visit_data.get('startTime') or
                            segment.get('startTime')
                        )
                        points.append({
                            'lat': coords[0],
                            'lon': coords[1],
                            'timestamp': timestamp,
                            'placeID': top_candidate.get('placeID'),
                            'semanticType': top_candidate.get('semanticType', 'Unknown Location'),
                            'probability': float(top_candidate.get('probability', 0)) if top_candidate.get('probability') else 0.0,
                            'source': 'visit'
                        })

            elif config["INCLUDE_ACTIVITIES"] and 'activity' in segment:
                activity = segment.get('activity', {})
                activity_type = activity.get('topCandidate', {}).get('type', 'Unknown')
                if start_lat_lng := activity.get('start', {}).get('latLng'):
                    if coords := parse_lat_lng_string(start_lat_lng):
                        timestamp = _parse_timestamp(activity.get('start', {}).get('time') or segment.get('startTime'))
                        points.append({
                            'lat': coords[0],
                            'lon': coords[1],
                            'timestamp': timestamp,
                            'placeID': None,
                            'semanticType': f'Activity ({activity_type})',
                            'probability': 0.0,
                            'source': 'activity'
                        })
                if end_lat_lng := activity.get('end', {}).get('latLng'):
                    if coords := parse_lat_lng_string(end_lat_lng):
                        timestamp = _parse_timestamp(activity.get('end', {}).get('time') or segment.get('endTime'))
                        points.append({
                            'lat': coords[0],
                            'lon': coords[1],
                            'timestamp': timestamp,
                            'placeID': None,
                            'semanticType': f'Activity ({activity_type})',
                            'probability': 0.0,
                            'source': 'activity'
                        })
        except Exception:
            print(f"\n[WARNING] Error processing segment #{i+1}. Skipping.")
            continue
        if (i + 1) % 20000 == 0:
            print(f"  [PROGRESS] {i+1:,} segments processed...")
    return points

def _process_timeline_objects_format(file_handle, config):
    """Processes the newer 'timelineObjects' (iOS) format."""
    print("[INFO] 'timelineObjects' (iOS) format detected. Processing...")
    points = []
    E7 = 1e-7
    timeline_objects = ijson.items(file_handle, 'timelineObjects.item')

    for i, t_object in enumerate(timeline_objects):
        try:
            if config["INCLUDE_VISITS"] and 'placeVisit' in t_object:
                place_visit = t_object.get('placeVisit', {})
                if location := place_visit.get('location', {}):
                    if 'latitudeE7' in location and 'longitudeE7' in location:
                        # Extract timestamp and metadata from duration
                        timestamp = _parse_timestamp(
                            place_visit.get('duration', {}).get('startTimestamp') or
                            place_visit.get('duration', {}).get('startTimestampMs')
                        )
                        # iOS format may have semanticType in location
                        semantic_type = location.get('semanticType') or place_visit.get('semanticType', 'Unknown Location')
                        place_id = location.get('placeId') or place_visit.get('placeId')
                        points.append({
                            'lat': location['latitudeE7'] * E7,
                            'lon': location['longitudeE7'] * E7,
                            'timestamp': timestamp,
                            'placeID': place_id,
                            'semanticType': semantic_type,
                            'probability': 0.0,  # iOS format doesn't provide probability
                            'source': 'visit'
                        })

            elif config["INCLUDE_ACTIVITIES"] and 'activitySegment' in t_object:
                segment = t_object.get('activitySegment', {})
                start_time = _parse_timestamp(
                    segment.get('duration', {}).get('startTimestamp') or
                    segment.get('duration', {}).get('startTimestampMs')
                )
                end_time = _parse_timestamp(
                    segment.get('duration', {}).get('endTimestamp') or
                    segment.get('duration', {}).get('endTimestampMs')
                )
                activity_type = segment.get('activityType', 'Unknown')

                if start_loc := segment.get('startLocation'):
                    if 'latitudeE7' in start_loc and 'longitudeE7' in start_loc:
                        points.append({
                            'lat': start_loc['latitudeE7'] * E7,
                            'lon': start_loc['longitudeE7'] * E7,
                            'timestamp': start_time,
                            'placeID': None,
                            'semanticType': f'Activity ({activity_type})',
                            'probability': 0.0,
                            'source': 'activity'
                        })

                if end_loc := segment.get('endLocation'):
                    if 'latitudeE7' in end_loc and 'longitudeE7' in end_loc:
                        points.append({
                            'lat': end_loc['latitudeE7'] * E7,
                            'lon': end_loc['longitudeE7'] * E7,
                            'timestamp': end_time,
                            'placeID': None,
                            'semanticType': f'Activity ({activity_type})',
                            'probability': 0.0,
                            'source': 'activity'
                        })

                if config["INCLUDE_RAW_PATH"] and (raw_path := segment.get('simplifiedRawPath')):
                    raw_points = raw_path.get('points', [])
                    for idx, point in enumerate(raw_points):
                        if 'latE7' in point and 'lngE7' in point:
                            # Try to interpolate timestamp for path points
                            point_time = None
                            if config["INTERPOLATE_MISSING_TIMESTAMPS"] and start_time and end_time:
                                progress = idx / max(len(raw_points) - 1, 1)
                                point_time = int(start_time + (end_time - start_time) * progress)
                            points.append({
                                'lat': point['latE7'] * E7,
                                'lon': point['lngE7'] * E7,
                                'timestamp': point_time,
                                'placeID': None,
                                'semanticType': None,
                                'probability': 0.0,
                                'source': 'path'
                            })
        except Exception:
            print(f"\n[WARNING] Error processing timeline object #{i+1}. Skipping.")
            continue
        if (i + 1) % 20000 == 0:
            print(f"  [PROGRESS] {i+1:,} timeline objects processed...")
    return points

def _process_root_array_format(file_handle, config):
    """
    Processes a JSON format where the root is a direct array of records.
    This format also contains 'visit' and 'activity' objects.
    """
    print("[INFO] Root array format detected. Processing...")
    points = []
    # This regex helper function is reused from the semantic segments parser.
    coord_regex = re.compile(r"([-]?\d+\.\d+)")
    def parse_lat_lng_string(lat_lng_str):
        if not isinstance(lat_lng_str, str): return None
        try:
            # It finds the two floating point numbers in strings like "geo:35.123,-47.456"
            coords = [float(c) for c in coord_regex.findall(lat_lng_str)]
            return [coords[0], coords[1]] if len(coords) == 2 else None
        except (ValueError, AttributeError): return None

    # The '.item' suffix tells ijson to iterate through the items of the root array.
    records = ijson.items(file_handle, 'item')

    for i, record in enumerate(records):
        try:
            # Check if the object is a 'visit'.
            if config["INCLUDE_VISITS"] and 'visit' in record:
                if lat_lng := record.get('visit', {}).get('topCandidate', {}).get('placeLocation'):
                    if coords := parse_lat_lng_string(lat_lng):
                        # Extract timestamp and metadata from visit
                        visit_data = record.get('visit', {})
                        top_candidate = visit_data.get('topCandidate', {})
                        timestamp = _parse_timestamp(
                            record.get('visit', {}).get('startTime') or
                            record.get('startTime')
                        )
                        points.append({
                            'lat': coords[0],
                            'lon': coords[1],
                            'timestamp': timestamp,
                            'placeID': top_candidate.get('placeID'),
                            'semanticType': top_candidate.get('semanticType', 'Unknown Location'),
                            'probability': float(top_candidate.get('probability', 0)) if top_candidate.get('probability') else 0.0,
                            'source': 'visit'
                        })

            # Check if the object is an 'activity'.
            elif config["INCLUDE_ACTIVITIES"] and 'activity' in record:
                activity = record.get('activity', {})
                if start_coords := parse_lat_lng_string(activity.get('start')):
                    timestamp = _parse_timestamp(
                        activity.get('startTime') or
                        record.get('startTime')
                    )
                    activity_type = activity.get('topCandidate', {}).get('type', 'Unknown')
                    points.append({
                        'lat': start_coords[0],
                        'lon': start_coords[1],
                        'timestamp': timestamp,
                        'placeID': None,
                        'semanticType': f'Activity ({activity_type})',
                        'probability': 0.0,
                        'source': 'activity'
                    })
                if end_coords := parse_lat_lng_string(activity.get('end')):
                    timestamp = _parse_timestamp(
                        activity.get('endTime') or
                        record.get('endTime')
                    )
                    activity_type = activity.get('topCandidate', {}).get('type', 'Unknown')
                    points.append({
                        'lat': end_coords[0],
                        'lon': end_coords[1],
                        'timestamp': timestamp,
                        'placeID': None,
                        'semanticType': f'Activity ({activity_type})',
                        'probability': 0.0,
                        'source': 'activity'
                    })

        except Exception:
            # If an error occurs processing a single record, skip it and continue.
            print(f"\n[WARNING] Error processing record #{i+1}. Skipping.")
            continue

        if (i + 1) % 20000 == 0:
            print(f"  [PROGRESS] {i+1:,} records processed...")

    return points

def extract_locations(config):
    """
    Detects the JSON format by sniffing the file's start
    and calls the appropriate processing function.
    Handles all known formats: root array, 'locations', 'semanticSegments', or 'timelineObjects'.
    """
    print("\n--- [PHASE 1/3] Processing JSON File ---")
    input_file = config["JSON_INPUT_FILE"]
    print(f"[INFO] Starting to read '{input_file}'...")
    
    points = []

    try:
        with open(input_file, 'rb') as f:
            # Sniff the first few non-whitespace bytes to detect the root structure.
            prefix = f.read(4096).strip()
            f.seek(0) # Rewind the file for the actual parser.
            
            detected_format = None
            
            # Check if the file starts with '[' for the root array format.
            if prefix.startswith(b'['):
                detected_format = 'root_array'
            # Otherwise, check for known keys if it's an object.
            elif prefix.startswith(b'{'):
                if b'"locations"' in prefix:
                    detected_format = 'locations'
                elif b'"semanticSegments"' in prefix:
                    detected_format = 'semanticSegments'
                elif b'"timelineObjects"' in prefix:
                    detected_format = 'timelineObjects'

            # Call the correct function based on the detected format.
            if detected_format == 'root_array':
                points = _process_root_array_format(f, config)
            elif detected_format == 'locations':
                points = _process_locations_format(f)
            elif detected_format == 'semanticSegments':
                points = _process_semantic_segments_format(f, config)
            elif detected_format == 'timelineObjects':
                points = _process_timeline_objects_format(f, config)
            else:
                print("\n[ERROR] Could not determine JSON format. No known structure was identified.")
                return None

    except ijson.common.IncompleteJSONError as e:
        print(f"\n[STRUCTURAL ERROR] A parsing error occurred: {e}")
        print("  > ACTION: Proceeding with the data read so far.")
    except FileNotFoundError:
        print(f"\n[FATAL ERROR] The input file '{input_file}' was not found.")
        return None
    except Exception as e:
        print(f"\n[FATAL ERROR] An unexpected error occurred: {e}")
        traceback.print_exc()
        return None

    # --- Final Processing Report ---
    print("\n[INFO] File analysis complete.")
    print(f"  > Total coordinate points found: {len(points):,}")

    if not points:
        print("\n[WARNING] No location points were extracted. The HTML file will not be generated.")
        return None
    
    return points

def create_html_file(config, points):
    """Generates the final HTML file, injecting all data and configurations."""
    print("\n--- [PHASE 2/3] Generating Interactive HTML File ---")
    output_file = config["HTML_OUTPUT_FILE"]
    print(f"[INFO] Creating '{output_file}' with live controls...")

    # Prepare initial heatmap options for JavaScript injection.
    heatmap_options_js = json.dumps({
        "radius": config["HEATMAP_RADIUS"],
        "blur": config["HEATMAP_BLUR"],
        "max": config["HEATMAP_MAX_INTENSITY"],
        "maxZoom": config["HEATMAP_MAX_ZOOM"],
        "minOpacity": config["HEATMAP_MIN_OPACITY"],
        "gradient": config["HEATMAP_GRADIENT"]
    })

    # Prepare time filtering configuration for JavaScript injection.
    time_config_js = json.dumps({
        "enabled": config["ENABLE_TIME_FILTER"],
        "grouping": config["TIME_GROUPING"],
        "mode": config["TIME_FILTER_MODE"],
        "animationSpeed": config["ANIMATION_SPEED"],
        "animationLoop": config["ANIMATION_LOOP"],
        "smoothTransitions": config["SMOOTH_TRANSITIONS"]
    })

    # Prepare marker layer configuration for JavaScript injection.
    marker_config_js = json.dumps({
        "enabled": config["ENABLE_MARKERS"],
        "visibleByDefault": config["MARKERS_VISIBLE_BY_DEFAULT"],
        "maxMarkers": config["MAX_MARKERS"],
        "clusterRadius": config["MARKER_CLUSTER_RADIUS"],
        "minVisits": config["MARKER_MIN_VISITS"],
        "includePathInMarkers": config["INCLUDE_PATH_IN_MARKERS"]
    })

    # Pass the map style dictionaries to JavaScript.
    map_styles_js = json.dumps(MAP_STYLE_URLS)
    map_attributions_js = json.dumps(MAP_ATTRIBUTIONS)

    # Replace all placeholders in the template with configured values.
    final_html = (
        HTML_TEMPLATE
        .replace("%(LOCATIONS_DATA)s", json.dumps(points))
        .replace("%(HEATMAP_OPTIONS)s", heatmap_options_js)
        .replace("%(TIME_CONFIG)s", time_config_js)
        .replace("%(MARKER_CONFIG)s", marker_config_js)
        .replace("%(MAP_CENTER)s", str(config["MAP_INITIAL_CENTER"]))
        .replace("%(MAP_ZOOM)s", str(config["MAP_INITIAL_ZOOM"]))
        .replace("%(INITIAL_MAP_STYLE)s", config["MAP_STYLE"])
        .replace("%(MAP_STYLES_JS)s", map_styles_js)
        .replace("%(MAP_ATTRIBUTIONS_JS)s", map_attributions_js)
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    file_size_kb = os.path.getsize(output_file) / 1024
    print(f"[SUCCESS] File '{output_file}' generated ({file_size_kb:.2f} KB).")

def open_in_browser(config):
    """Opens the generated HTML file in the default web browser."""
    if not config["AUTO_OPEN_IN_BROWSER"]: return
    print("\n--- [PHASE 3/3] Visualization ---")
    file_name = config["HTML_OUTPUT_FILE"]
    print(f"[INFO] Opening '{file_name}' in your default browser...")
    absolute_path = os.path.abspath(file_name)
    webbrowser.open(f"file://{absolute_path}")

def main():
    """Main function that orchestrates the entire script execution."""
    print("="*60)
    print(">>> HEATMAP GENERATOR SCRIPT STARTING <<<")
    print("="*60)
    location_points = extract_locations(CONFIG)
    if location_points:
        create_html_file(CONFIG, location_points)
        open_in_browser(CONFIG)
    else:
        print("\n[EXECUTION FINISHED] No data was extracted, HTML file not generated.")
    print("\n" + "="*60)
    print(">>> SCRIPT EXECUTION FINISHED <<<")
    print("="*60)

if __name__ == '__main__':
    main()