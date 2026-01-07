# Google Location History Heatmap Generator (Enhanced)

An enhanced fork of [timeline_google-maps](https://github.com/rubensbraz/timeline_google-maps) by Rubens Braz, adding **interactive time-based filtering, animation features, and a privacy-focused web app** to visualize your location history.

## 🌐 Two Ways to Use

### Option 1: Web App (Recommended for Most Users)
**No Python installation required!** Visit the web app and upload your Google Takeout file:

👉 **[Launch Web App](https://timeline-google-maps.vercel.app/)**

- ✅ **100% Private** - All processing happens in your browser, your data never leaves your device
- ✅ **No Installation** - Works in any modern browser (Chrome, Firefox, Safari, Edge)
- ✅ **Mobile-Friendly** - Fully responsive design with touch support
- ✅ **All Features** - Complete feature parity with Python script (markers, time filters, animations)
- ✅ **Drag & Drop** - Simply drag your JSON file to visualize

### Option 2: Python Script (For Power Users)
Use the command-line Python script for maximum configurability and automation.

![Heatmap Screenshot](example.png)

## New Features in This Fork

### Interactive Location Markers with Visit Statistics
- **Clickable Markers**: Click any location to see detailed visit statistics
- **Smart Clustering**: Markers automatically cluster at different zoom levels
  - Zoomed out: Clusters show neighborhood-level aggregations
  - Zoomed in: Individual locations with precise details
- **Visit Analytics**: Each marker displays:
  - Total visits and unique days visited
  - Longest consecutive visit streak
  - First and last visit dates
  - Semantic location type from Google ("Home", "Work", "Activity", etc.)
- **Performance Optimized**: Handles large datasets with spatial indexing and configurable marker limits
- **Synchronized Filtering**: Markers update automatically with time-based filters

### Time-Based Filtering & Animation
- **Three visualization modes**:
  - **Static Mode**: View all your location data at once (original behavior)
  - **Date Range Mode**: Select a custom date range (e.g., Jan 2015 - Dec 2025) to see all locations within that period, with optional slider to drill down into individual months/years
  - **Animation Mode**: Watch your location history play through time with smooth transitions

- **Time Grouping**: Toggle between monthly and yearly views
- **Smooth Transitions**: Beautiful blend animations between time periods (not jarring jumps)
- **Playback Controls**: Play/pause, step forward/backward, adjustable speed, and loop options
- **Timestamp Interpolation**: Intelligently handles missing timestamps in path data
- **Real-time Statistics**: See point counts and date ranges for current view

### Enhanced Configuration
All features are configurable through the `CONFIG` dictionary:
```python
# Time Filtering
"ENABLE_TIME_FILTER": True,
"TIME_GROUPING": "monthly",        # or "yearly"
"TIME_FILTER_MODE": "static",      # "static", "daterange", or "animation"
"ANIMATION_SPEED": 100,            # milliseconds per frame
"ANIMATION_LOOP": False,
"SMOOTH_TRANSITIONS": True,

# Location Markers
"ENABLE_MARKERS": True,
"MARKERS_VISIBLE_BY_DEFAULT": True,
"MAX_MARKERS": 5000,               # Performance limit
"MARKER_CLUSTER_RADIUS": 50,
"MARKER_MIN_VISITS": 1,
```

## Original Features

- **Privacy First**: All processing is done locally on your machine. Your location data is never uploaded.
- **Universal Parser**: Automatically detects and parses both the old (`locations`) and new (`semanticSegments`) formats of Google's location history.
- **Efficient**: Uses a streaming JSON parser (`ijson`) to handle multi-gigabyte data files with low memory usage.
- **Interactive UI**: The generated HTML file includes a live control panel to customize the visualization in real-time.
- **Self-Contained Output**: The script generates a single `heatmap.html` file with all necessary CSS and JavaScript embedded.

## How to Use

### Step 1: Get Your Location Data

#### Android
1. Go to your device's main Settings menu, not within the Google Maps app itself.
2. Navigate to the Location menu.
3. Select Location Services.
4. Tap on Timeline.
5. Export timeline data.
6. Once exported, place the `.json` file inside the repository directory.

#### iOS
1. Open the Google Maps app.
2. Tap your profile picture in the top-right corner, then select "Your timeline".
3. Tap the "..." (three dots) icon at the top right, then select "Location and privacy settings".
4. Scroll down and tap "Export Timeline Data".
5. Save the file to your phone, then transfer it to your computer.
6. Once exported, place the `.json` file inside the repository directory.

### Step 2: Set Up the Environment

1. **Clone the repository** or download the `generate_heatmap.py` script.
2. **Place your `Records.json`** file in the same directory as the script.
3. **Install the required Python package**:
   ```bash
   pip install -r requirements.txt
   ```

### Step 3: Configure and Run the Script

1. **(Optional) Customize the initial view**: Open the `generate_heatmap.py` file and edit the `CONFIG` dictionary at the top to set your preferred initial zoom, map center, colors, time filtering options, and other defaults.
2. **Run the script** from your terminal:
   ```bash
   python generate_heatmap.py
   ```
   (On macOS/Linux, you may need to use `python3` instead)
3. The script will process your data and automatically open the generated `heatmap.html` file in your default web browser.

## Understanding the Live Controls

### Heatmap Controls
- **Map Style**: Changes the underlying base map. "OpenStreetMap" is often best for viewing the heatmap.
- **Radius**: Increases or decreases the size of the "glow" for each data point.
- **Blur**: Adjusts the smoothness of the heat areas.
- **Max Intensity**: A powerful setting for tuning the map's "sensitivity". A **lower** value makes the map appear "hotter" with less data, ideal for sparse histories. A **higher** value requires a greater concentration of data to show "hot" (red) areas.
- **Heatmap Max Zoom**: An advanced setting that controls the zoom level at which the heatmap is rendered at its highest detail.

### Location Marker Controls
- **Show Location Markers**: Toggle clickable markers on/off (green dots and clusters)
- **Click Individual Markers**: See detailed visit statistics for that location
- **Click Clusters**: View aggregated statistics for all locations in that cluster
- **Zoom In/Out**: Watch clusters automatically split or merge based on zoom level

### Time Filter Controls
- **Time Filter Mode**: Choose between Static (all data), Date Range (custom range), or Animation (auto-play through time)
- **Time Grouping**: Switch between monthly and yearly time periods
- **Date Range Selectors**: Pick start and end months/years for custom date ranges
- **Set Range Button**: Apply your selected date range to view all locations within that period
- **Timeline Slider**: Drill down into individual time periods within your selected range
- **Animation Controls**: Play/pause, step forward/backward through time periods
- **Animation Speed**: Adjust how fast the animation plays
- **Loop Animation**: Toggle whether animation repeats from the beginning
- **Smooth Transitions**: Enable/disable blending between time periods

## Attribution

This is an enhanced fork of the original [timeline_google-maps](https://github.com/rubensbraz/timeline_google-maps) project.

**Original Author**: Rubens Braz ([rubensbrazf@gmail.com](mailto:rubensbrazf@gmail.com))

**Enhancements**: Interactive location markers with visit statistics, time-based filtering, animation system, and enhanced UI controls

## License

This project is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](LICENSE) - the same license as the original project.

[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-shield]: https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png
