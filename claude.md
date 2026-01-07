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

**Current Architecture (Python Script):**
- All HTML, CSS, and JavaScript embedded in `generate_heatmap.py`
- Output: Standalone `heatmap.html` (8-10MB with typical dataset)
- No external dependencies beyond CDN libraries (Leaflet, Leaflet.heat, Leaflet.markercluster)

**Dependencies:**
- Python: `ijson` for streaming JSON parsing
- JavaScript: Leaflet 1.9.4, Leaflet.heat 0.2.0, Leaflet.markercluster 1.5.3

---

## Web App Version (Planned - Client-Side Processing)

### Objectives
Create a privacy-focused web application that allows non-technical users to visualize their Google Location History without installing Python. All processing happens **entirely in the browser** - no data ever leaves the user's device.

### Core Principles
1. **Zero Data Upload** - File processing via FileReader API (client-side only)
2. **Maximum Privacy** - No tracking, no analytics, no server-side processing
3. **No Installation** - Works in any modern browser
4. **Feature Parity** - All features from Python script (markers, time filters, etc.)
5. **Single HTML File** - Entire app in one file (vanilla JS, no build step)

### Technical Architecture

**State Management:**
```javascript
LANDING    → User uploads JSON file (drag & drop)
PROCESSING → Client-side parsing & processing (progress indicator)
MAP_VIEW   → Interactive map with all features
```

**Key Components:**
1. **Landing Page**
   - File upload zone (drag & drop + click to select)
   - Instructions (Android/iOS/Desktop paths to get data)
   - Privacy badges ("Your data never leaves your device")

2. **Parser Functions** (Port from Python → JavaScript)
   - `parseTimestamp()` - Handle all Google timestamp formats
   - `detectFormat()` - Identify JSON structure (4 formats supported)
   - `processLocationsFormat()` - Old format with E7 coordinates
   - `processSemanticSegmentsFormat()` - Android format with geo strings
   - `processTimelineObjectsFormat()` - iOS format
   - `processRootArrayFormat()` - Direct array format

3. **Processing Pipeline**
   ```
   File Upload → FileReader → JSON.parse() → Format Detection
       → Parser (JS version) → Processed Data → Map Initialization
   ```

4. **Map Interface**
   - Reuse existing map code from Python template (already JavaScript)
   - Auto-center map based on data bounds
   - All existing features work (markers, clustering, time filters)

### Implementation Strategy

**Phase 1: Core Functionality**
- HTML skeleton with 3 states (landing/processing/map)
- Port 4 parser functions to JavaScript
- File upload handling
- Progress indicators

**Phase 2: Map Integration**
- Extract map initialization code from Python template
- Auto-center on data
- Ensure all controls work

**Phase 3: Polish**
- Responsive design (mobile-friendly)
- Error handling (invalid JSON, large files, wrong format)
- Instructions with screenshots
- Accessibility (ARIA labels, keyboard nav)

**Phase 4: Deployment**
- Deploy to Netlify/Vercel
- Single-file deployment (index.html only)
- HTTPS automatic
- Custom domain (optional)

### Performance Considerations

**Large File Handling:**
- Chunked processing (10,000 records at a time)
- Progress updates every chunk
- `setTimeout(0)` to prevent UI freezing
- Memory cleanup after processing

**Mobile Optimization:**
- Reduce MAX_MARKERS to 2000 on mobile
- Disable smooth transitions (performance)
- Simplified cluster icons

**Browser Compatibility:**
- FileReader API (95%+ browser support)
- Fallback error messages for old browsers
- Tested on Chrome, Firefox, Safari, Edge

### Security & Privacy

**Client-Side Guarantees:**
- Zero network requests after page load (verifiable in DevTools)
- No localStorage/IndexedDB (no persistence)
- No third-party scripts (only CDN libraries: Leaflet)
- No analytics or tracking
- Open source (full transparency)

**User Trust Indicators:**
- "🔒 Your data never leaves your device" badge
- Network tab shows no uploads
- Open source code visible
- Link to Python script for paranoid users

### Deployment Structure

```
/
├── index.html          # Single-file web app (NEW)
├── generate_heatmap.py # Python script (keep for power users)
├── netlify.toml        # Deploy config
├── README.md           # Updated with web app link
└── /docs               # Screenshots/guides (optional)
```

### Success Metrics

- [ ] Drag & drop file upload works
- [ ] All 4 Google Takeout formats supported
- [ ] Map renders with all features
- [ ] No network traffic during processing (verified)
- [ ] Works on mobile devices
- [ ] Clear error messages for edge cases
- [ ] Deployed and publicly accessible
- [ ] Documentation updated

### Future Enhancements (Post-Launch)

**Nice-to-Have:**
- Download as HTML (generate standalone file like Python script)
- Dark mode toggle
- Export visit statistics as CSV
- PWA features (offline support, install as app)
- Multi-file support (combine multiple exports)
- Advanced settings panel (customize config before processing)

**Will NOT Include:**
- Data upload to server
- User accounts/login
- Data persistence (IndexedDB caching)
- Analytics/tracking
- Monetization

---

**Implementation Status:** ✅ **COMPLETE** - Fully functional web app deployed
**Implementation:** See `index.html` (2,130 lines, single-file web app)
**Deployment:** Vercel (or any static host)
