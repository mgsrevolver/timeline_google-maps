# Time-Based Heatmap Filtering Implementation Plan

## Goal
Add interactive date range filtering to the location history heatmap, allowing users to visualize their location data over specific time periods with animation capabilities.

## Current State
- Script uses Leaflet.js with custom HTML template
- Has beautiful collapsible controls panel with live sliders
- Supports multiple data formats (locations, semanticSegments, timelineObjects, root array)
- Currently displays ALL location data at once (no time filtering)

## Implementation Approach

### 1. Data Extraction Changes (Python)
**File:** `generate_heatmap.py`

#### Modify Parser Functions
Each parser function needs to extract timestamps alongside coordinates:
- `_process_locations_format()` - Extract `timestamp` or `timestampMs`
- `_process_semantic_segments_format()` - Extract from visit/activity start/end times
- `_process_timeline_objects_format()` - Extract from placeVisit/activitySegment duration
- `_process_root_array_format()` - Extract from visit/activity timestamps

#### Data Structure Change
**Current:** `points = [[lat, lon], [lat, lon], ...]`
**New:** `points = [[lat, lon, timestamp], [lat, lon, timestamp], ...]`

Where timestamp is Unix epoch milliseconds (JavaScript-compatible)

#### Add Configuration Options
```python
CONFIG = {
    # ... existing config ...

    # --- Time Filtering Settings ---
    "ENABLE_TIME_FILTER": True,
    "TIME_GROUPING": "monthly",  # Options: 'daily', 'weekly', 'monthly', 'yearly'
    "ANIMATION_SPEED": 1000,     # Milliseconds per frame
}
```

### 2. HTML/JavaScript Changes

#### Add Date Range Controls to Control Panel
Add new control group in the `#controls-content` div:
```html
<div class="control-group">
    <label for="dateRange">Date Range</label>
    <input type="date" id="dateStart" />
    <input type="date" id="dateEnd" />
    <button id="resetDateRange">Reset</button>
</div>

<div class="control-group">
    <label for="timeSlider">Timeline <span id="currentPeriod" class="value-display"></span></label>
    <input type="range" id="timeSlider" min="0" max="100" step="1">
    <div class="playback-controls">
        <button id="playPause">▶️ Play</button>
        <button id="stepBack">⏮️</button>
        <button id="stepForward">⏭️</button>
    </div>
</div>
```

#### JavaScript Data Processing
1. **Parse time-stamped data** on page load
2. **Group data by time periods** (daily/weekly/monthly)
3. **Create time index** for slider navigation
4. **Filter visible points** based on selected date range
5. **Implement animation** with play/pause controls

#### Core Functions Needed
```javascript
// Group location data by time periods
function groupDataByTimePeriod(data, grouping) { ... }

// Filter data based on date range
function filterDataByDateRange(data, startDate, endDate) { ... }

// Update heatmap with filtered data
function updateHeatmapData(filteredData) { ... }

// Animation controller
function playAnimation() { ... }
function stopAnimation() { ... }
```

### 3. UI/UX Considerations

#### Time Period Display
- Show current time period in readable format (e.g., "January 2020")
- Display total points in current view
- Show date range summary

#### Performance Optimization
- Pre-compute time groups on load
- Use efficient filtering (don't rebuild entire heatmap each frame)
- Consider data decimation for very large datasets

#### Animation Features
- Smooth transitions between time periods
- Adjustable playback speed
- Loop option
- Frame-by-frame stepping

## Implementation Steps

### Phase 1: Backend Data Processing
1. Modify each parser function to extract timestamps
2. Add timestamp normalization (handle different formats)
3. Update data structure to include timestamps
4. Add fallback handling for records without timestamps

### Phase 2: Frontend Time Controls
1. Add date range input controls to HTML
2. Calculate min/max dates from data
3. Implement date range filtering logic
4. Update heatmap when date range changes

### Phase 3: Timeline Slider & Animation
1. Add timeline slider control
2. Group data by time periods
3. Implement slider-based time navigation
4. Add play/pause functionality
5. Add step forward/backward controls

### Phase 4: Polish & Optimization
1. Add loading indicators for large datasets
2. Optimize filtering performance
3. Add visual feedback (point counts, date labels)
4. Test with different data formats
5. Add error handling for edge cases

## Technical Challenges

### Challenge 1: Timestamp Format Variations
Different Google Takeout formats use different timestamp representations:
- `timestampMs` (string) - milliseconds since epoch
- `timestamp` (string) - ISO 8601 format
- `startTime`/`endTime` objects with various formats

**Solution:** Create unified timestamp parser that handles all formats

### Challenge 2: Missing Timestamps
Some records may not have timestamps (especially in raw path data)

**Solution:**
- Use segment-level timestamp for all points within that segment
- Filter out points without timestamps, or
- Interpolate timestamps for path points

### Challenge 3: Performance with Large Datasets
Filtering millions of points on every slider change could be slow

**Solution:**
- Pre-group data by time periods
- Use efficient data structures (Map/Set)
- Implement data decimation/clustering for dense areas
- Consider Web Workers for heavy processing

### Challenge 4: Smooth Heatmap Updates
Leaflet.heat may flicker when updating data

**Solution:**
- Use `setLatLngs()` method instead of removing/re-adding layer
- Batch updates to minimize redraws
- Add CSS transitions for smoother visual changes

## File Changes Summary

### Modified Files
- `generate_heatmap.py` - All parser functions + HTML template

### New Files (Optional)
- Could separate JavaScript into external file for cleaner code
- Could add CSS file for time control styling

## Next Steps
1. Review this plan and confirm approach
2. Decide on time grouping strategy (monthly vs weekly vs daily)
3. Implement Phase 1 (backend data extraction)
4. Test with sample data
5. Proceed to frontend implementation

## Questions to Resolve
1. Should we support all time groupings or start with just monthly?
2. Do we want cumulative view (show all data up to selected date) or window view (show only selected period)?
3. Should animation loop by default?
4. What should happen to points without timestamps - skip them or show in all time periods?
