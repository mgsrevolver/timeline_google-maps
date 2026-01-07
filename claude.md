# Google Location History Heatmap - Enhanced Features

Enhanced fork of timeline_google-maps with interactive time-based filtering and clickable location markers.

## Feature Overview

### 1. Interactive Location Markers (✓ Implemented)
Clickable markers with detailed visit statistics, leveraging Google's semantic metadata that was previously discarded.

**Key Components:**
- **Data Preservation**: All parsers modified to capture `placeID`, `semanticType`, `probability`, and `source`
- **Spatial Indexing**: Points grouped by ~11m grid cells for efficient clustering
- **Leaflet.markercluster**: Automatic zoom-based clustering with aggregation
- **Visit Analytics**: Total visits, unique days, consecutive streaks, semantic labels

**Configuration:**
```python
"ENABLE_MARKERS": True,
"MARKERS_VISIBLE_BY_DEFAULT": True,
"MAX_MARKERS": 5000,
"MARKER_CLUSTER_RADIUS": 50,
"MARKER_MIN_VISITS": 1,
"INCLUDE_PATH_IN_MARKERS": False,
```

**Performance:**
- Spatial index for O(1) lookups
- Marker decimation when exceeding MAX_MARKERS
- Cluster click aggregation limited to 500 markers
- Error handling prevents marker failures from breaking controls

### 2. Time-Based Filtering & Animation (✓ Implemented)
Dynamic visualization of location history across time periods with smooth transitions.

**Modes:**
- **Static**: Show all data (default)
- **Date Range**: Custom time window with drill-down slider
- **Animation**: Auto-play through time with configurable speed

**Configuration:**
```python
"ENABLE_TIME_FILTER": True,
"TIME_GROUPING": "monthly",
"TIME_FILTER_MODE": "static",
"ANIMATION_SPEED": 100,
"ANIMATION_LOOP": False,
"SMOOTH_TRANSITIONS": True,
"INTERPOLATE_MISSING_TIMESTAMPS": True,
```

**Integration:**
- Markers automatically sync with time filter changes
- Smooth blend transitions between periods (8 frames, 30ms each)
- Data grouped by period includes both heatmap points and full marker data

## Data Structure

**Current Format:**
```javascript
locationData = [
    {
        lat: float,
        lon: float,
        timestamp: int,        // Unix epoch milliseconds
        placeID: string,       // Google Places ID
        semanticType: string,  // "Inferred Home", "Work", etc.
        probability: float,    // Confidence score
        source: string         // "visit", "activity", "path"
    },
    ...
]
```

**Backward Compatibility:**
- Heatmap layer extracts `[lat, lon]` from objects
- Time filtering groups include both `points` (for heatmap) and `fullData` (for markers)

## Architecture Notes

### Parser Functions (Python)
All 4 formats preserve metadata:
- `_process_locations_format()` - Old format (minimal metadata)
- `_process_semantic_segments_format()` - Android format (rich metadata)
- `_process_timeline_objects_format()` - iOS format
- `_process_root_array_format()` - Direct array format

### JavaScript Organization
1. **Map Initialization** (lines 364-373): Create map, heatmap layer
2. **Marker Layer** (lines 375-626): Spatial index, stats calculator, clustering
3. **Controls Logic** (lines 628-690): UI event handlers
4. **Time Filtering** (lines 691-1143): Period grouping, animation, date range
5. **Initialization** (lines 1162-1176): Set defaults, create markers

### Key Functions
- `buildSpatialIndex(data)` - Group points by grid coordinates
- `calculateVisitStats(points)` - Compute visit metrics
- `createMarkerLayer(data)` - Build clustered markers
- `groupDataByTimePeriod(data, grouping)` - Time-based data grouping
- `updateHeatmapForCurrentPeriod()` - Sync heatmap and markers

## Technical Decisions

### Spatial Indexing
- **Precision**: 4 decimal places (~11m radius)
- **Rationale**: Balance between grouping nearby points and distinguishing separate locations
- **Performance**: O(1) lookup during marker creation and cluster aggregation

### Metadata Priority
- **Semantic Type**: Highest probability wins; fallback to first non-null
- **Visit vs Activity**: Activities have no placeID, labeled as "Activity (type)"
- **Path Points**: Excluded from markers by default (configurable)

### Error Handling
- Marker initialization wrapped in try-catch to protect controls
- Time filter updates have isolated error handling
- Console logging for debugging without breaking UI

### Performance Limits
- **Max Markers**: 5000 default (configurable)
- **Cluster Aggregation**: 500 marker limit per cluster click
- **Decimation**: Even sampling when exceeding limits

## Future Enhancements

**Potential Features:**
- Heatmap/marker layer toggle (currently always overlaid)
- Custom marker colors by semantic type
- Export visit statistics to CSV
- Search/filter by location type
- Visit duration tracking (requires parsing duration data)
- Multi-select time ranges
- Custom spatial index precision based on zoom level

**API Integration (Optional):**
- Google Places API for place names using placeID
- Google Street View thumbnails in popups
- Reverse geocoding for activity points

## File Structure

**Single File Architecture:**
- All HTML, CSS, and JavaScript embedded in `generate_heatmap.py`
- Output: Standalone `heatmap.html` (8-10MB with typical dataset)
- No external dependencies beyond CDN libraries (Leaflet, Leaflet.heat, Leaflet.markercluster)

**Dependencies:**
- Python: `ijson` for streaming JSON parsing
- JavaScript: Leaflet 1.9.4, Leaflet.heat 0.2.0, Leaflet.markercluster 1.5.3
