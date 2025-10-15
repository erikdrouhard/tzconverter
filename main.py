import air
from tzconverter.timezones import (
    get_common_timezones,
    get_current_time_in_timezone,
    format_timezone_display,
    generate_24hour_slots,
    calculate_viability_score
)
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List
import uuid

app = air.Air()

# In-memory session storage (will be replaced by localStorage later)
sessions: Dict[str, List[Dict]] = {}


def get_session_id():
    """Generate or retrieve session ID (simplified for now)."""
    return "default"


def get_session_timezones():
    """Get timezones for current session."""
    session_id = get_session_id()
    return sessions.get(session_id, [])


def add_timezone_to_session(tz_id: str, tz_name: str):
    """Add timezone to session."""
    session_id = get_session_id()
    if session_id not in sessions:
        sessions[session_id] = []
    
    # Check if already exists
    for tz in sessions[session_id]:
        if tz["id"] == tz_id:
            return
    
    sessions[session_id].append({
        "id": tz_id,
        "name": tz_name,
        "preferred_start": 9,
        "preferred_end": 17,
        "uid": str(uuid.uuid4())
    })


def remove_timezone_from_session(uid: str):
    """Remove timezone from session by UID."""
    session_id = get_session_id()
    if session_id in sessions:
        sessions[session_id] = [tz for tz in sessions[session_id] if tz["uid"] != uid]


def update_timezone_hours(uid: str, start: int, end: int):
    """Update preferred hours for a timezone."""
    session_id = get_session_id()
    if session_id in sessions:
        for tz in sessions[session_id]:
            if tz["uid"] == uid:
                tz["preferred_start"] = start
                tz["preferred_end"] = end
                break


@app.get("/")
async def index():
    return air.Html(
        air.Head(
            air.Meta(charset="utf-8"),
            air.Meta(name="viewport", content="width=device-width, initial-scale=1"),
            air.Title("Timezone Meeting Scheduler"),
            air.Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"),
            air.Script(src="https://unpkg.com/htmx.org@1.9.10"),
            air.Script("""
                // Auto-refresh view when timezones change
                document.addEventListener('DOMContentLoaded', function() {
                    let currentView = null;
                    
                    // Track which view is active
                    document.addEventListener('htmx:afterRequest', function(evt) {
                        if (evt.detail.pathInfo.requestPath === '/grid') {
                            currentView = 'grid';
                        } else if (evt.detail.pathInfo.requestPath === '/converter') {
                            currentView = 'converter';
                        }
                        
                        // Refresh view after timezone changes
                        const refreshPaths = ['/add-timezone', '/remove-timezone', '/update-hours'];
                        if (refreshPaths.some(path => evt.detail.pathInfo.requestPath.includes(path))) {
                            if (currentView === 'grid') {
                                htmx.ajax('GET', '/grid', {target: '#view-content', swap: 'innerHTML'});
                            } else if (currentView === 'converter') {
                                htmx.ajax('GET', '/converter', {target: '#view-content', swap: 'innerHTML'});
                            }
                        }
                    });
                });
            """),
            air.Style("""
                .timezone-card {
                    margin-bottom: 1rem;
                    padding: 1rem;
                    border: 1px solid var(--pico-muted-border-color);
                    border-radius: var(--pico-border-radius);
                }
                .timezone-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 0.5rem;
                }
                .timezone-controls {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1rem;
                    margin-top: 0.5rem;
                }
                .view-toggle {
                    display: flex;
                    gap: 0.5rem;
                    margin: 1.5rem 0;
                }
                .view-content {
                    min-height: 200px;
                }
                #timezone-list:empty::before {
                    content: "No timezones selected. Add some above to get started!";
                    display: block;
                    padding: 2rem;
                    text-align: center;
                    color: var(--pico-muted-color);
                    font-style: italic;
                }
                
                /* Grid View Styles */
                .grid-container {
                    overflow-x: auto;
                    margin: 1rem 0;
                }
                .time-grid {
                    display: flex;
                    gap: 0.25rem;
                    min-width: max-content;
                    padding: 1rem 0;
                }
                .time-slot {
                    flex: 0 0 80px;
                    text-align: center;
                    cursor: pointer;
                    transition: transform 0.2s;
                    border-radius: var(--pico-border-radius);
                    padding: 1rem 0.5rem;
                    border: 2px solid transparent;
                }
                .time-slot:hover {
                    transform: translateY(-2px);
                    border-color: var(--pico-primary);
                }
                .time-slot.green {
                    background-color: #d4edda;
                    color: #155724;
                }
                .time-slot.yellow {
                    background-color: #fff3cd;
                    color: #856404;
                }
                .time-slot.red {
                    background-color: #f8d7da;
                    color: #721c24;
                }
                .time-slot-time {
                    font-weight: bold;
                    font-size: 1.1rem;
                    margin-bottom: 0.25rem;
                }
                .time-slot-score {
                    font-size: 0.85rem;
                }
                .grid-legend {
                    display: flex;
                    gap: 1rem;
                    justify-content: center;
                    margin-bottom: 1rem;
                    flex-wrap: wrap;
                }
                .legend-item {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                .legend-color {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                }
                .legend-color.green {
                    background-color: #d4edda;
                }
                .legend-color.yellow {
                    background-color: #fff3cd;
                }
                .legend-color.red {
                    background-color: #f8d7da;
                }
                
                /* Time Detail Modal */
                .time-detail {
                    margin-top: 1rem;
                    padding: 1rem;
                    border: 1px solid var(--pico-muted-border-color);
                    border-radius: var(--pico-border-radius);
                    background: var(--pico-background-color);
                }
                .time-detail-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                }
                .timezone-time-row {
                    display: flex;
                    justify-content: space-between;
                    padding: 0.5rem;
                    margin: 0.25rem 0;
                    border-radius: var(--pico-border-radius);
                }
                .timezone-time-row.in-hours {
                    background-color: #d4edda;
                }
                .timezone-time-row.out-hours {
                    background-color: #f8d7da;
                }
            """)
        ),
        air.Body(
            air.Main(
                {"class": "container"},
                air.H1("Timezone Meeting Scheduler"),
                air.P("Select timezones to find optimal meeting times across the globe."),
                
                # Timezone Selector
                air.Article(
                    air.H2("Add Timezone"),
                    air.Form(
                        {"hx-post": "/add-timezone", "hx-target": "#timezone-list", "hx-swap": "innerHTML"},
                        air.Div(
                            {"style": "display: grid; grid-template-columns: 1fr auto; gap: 1rem;"},
                            air.Select(
                                {"name": "timezone", "required": True},
                                air.Option("Select a timezone...", value=""),
                                *[air.Option(name, value=tz_id) for tz_id, name in get_common_timezones()]
                            ),
                            air.Button("Add Timezone", type="submit")
                        )
                    )
                ),
                
                # View Toggle Buttons
                air.Div(
                    {"class": "view-toggle"},
                    air.Button("Grid View", **{
                        "hx-get": "/grid",
                        "hx-target": "#view-content",
                        "hx-trigger": "click",
                        "id": "grid-view-btn"
                    }),
                    air.Button("Converter View", **{
                        "hx-get": "/converter",
                        "hx-target": "#view-content",
                        "hx-trigger": "click",
                        "id": "converter-view-btn"
                    })
                ),
                
                # Selected Timezones
                air.Article(
                    air.H2("Selected Timezones"),
                    air.Div({"id": "timezone-list"})
                ),
                
                # View Content Area
                air.Article(
                    air.H2("Meeting Time Finder"),
                    air.Div(
                        {"id": "view-content", "class": "view-content"},
                        air.P("Select a view above to analyze meeting times.")
                    )
                )
            )
        )
    )


@app.post("/add-timezone")
async def add_timezone(timezone: str = None):
    """Add a timezone to the session."""
    if not timezone:
        return render_timezone_list()
    
    # Find the display name
    tz_name = None
    for tz_id, name in get_common_timezones():
        if tz_id == timezone:
            tz_name = name
            break
    
    if tz_name:
        add_timezone_to_session(timezone, tz_name)
    
    return render_timezone_list()


@app.delete("/remove-timezone/{uid}")
async def remove_timezone(uid: str):
    """Remove a timezone from the session."""
    remove_timezone_from_session(uid)
    return render_timezone_list()


@app.post("/update-hours/{uid}")
async def update_hours(uid: str, start: int = 9, end: int = 17):
    """Update preferred hours for a timezone."""
    update_timezone_hours(uid, start, end)
    return render_timezone_list()


def render_timezone_list():
    """Render the list of timezone cards."""
    timezones = get_session_timezones()
    
    if not timezones:
        return air.Div()
    
    cards = []
    for tz in timezones:
        current_time = get_current_time_in_timezone(tz["id"])
        time_str = current_time.strftime("%I:%M %p")
        date_str = current_time.strftime("%A, %B %d, %Y")
        
        cards.append(
            air.Div(
                {"class": "timezone-card"},
                air.Div(
                    {"class": "timezone-header"},
                    air.Div(
                        air.Strong(tz["name"]),
                        air.Br(),
                        air.Small(f"{time_str} • {date_str}")
                    ),
                    air.Button(
                        "Remove",
                        **{
                            "hx-delete": f"/remove-timezone/{tz['uid']}",
                            "hx-target": "#timezone-list",
                            "hx-swap": "innerHTML",
                            "class": "secondary outline",
                            "style": "margin: 0;"
                        }
                    )
                ),
                air.Div(
                    {"class": "timezone-controls"},
                    air.Label(
                        "Preferred Start Time",
                        air.Input(
                            type="number",
                            name="start",
                            min="0",
                            max="23",
                            value=str(tz["preferred_start"]),
                            **{
                                "hx-post": f"/update-hours/{tz['uid']}",
                                "hx-trigger": "change",
                                "hx-target": "#timezone-list",
                                "hx-swap": "innerHTML",
                                "hx-include": "[name='end']"
                            }
                        ),
                        air.Small(f"{tz['preferred_start']}:00 ({tz['preferred_start'] % 12 or 12}{' AM' if tz['preferred_start'] < 12 else ' PM'})")
                    ),
                    air.Label(
                        "Preferred End Time",
                        air.Input(
                            type="number",
                            name="end",
                            min="0",
                            max="23",
                            value=str(tz["preferred_end"]),
                            **{
                                "hx-post": f"/update-hours/{tz['uid']}",
                                "hx-trigger": "change",
                                "hx-target": "#timezone-list",
                                "hx-swap": "innerHTML",
                                "hx-include": "[name='start']"
                            }
                        ),
                        air.Small(f"{tz['preferred_end']}:00 ({tz['preferred_end'] % 12 or 12}{' AM' if tz['preferred_end'] < 12 else ' PM'})")
                    )
                )
            )
        )
    
    return air.Div(*cards)


@app.get("/grid")
async def grid_view():
    """Show 24-hour grid with color-coded meeting time viability."""
    timezones = get_session_timezones()
    
    if not timezones:
        return air.Div(
            air.P("Please add at least one timezone to see the grid view."),
            {"style": "text-align: center; padding: 2rem; color: var(--pico-muted-color);"}
        )
    
    # Generate 24 hour slots starting from current UTC time's date
    base_time = datetime.now(ZoneInfo("UTC"))
    slots = generate_24hour_slots(base_time)
    
    # Build timezone config for viability calculation
    tz_config = [{
        "id": tz["id"],
        "preferred_start": tz["preferred_start"],
        "preferred_end": tz["preferred_end"]
    } for tz in timezones]
    
    # Create time slot elements
    time_slot_elements = []
    for slot in slots:
        score, color_class = calculate_viability_score(slot, tz_config)
        
        # Format the hour
        hour_24 = slot.hour
        hour_12 = hour_24 % 12 or 12
        am_pm = "AM" if hour_24 < 12 else "PM"
        time_str = f"{hour_12}{am_pm}"
        
        # Calculate percentage for display
        percentage = int(score * 100)
        
        time_slot_elements.append(
            air.Div(
                {
                    "class": f"time-slot {color_class}",
                    "hx-get": f"/grid-detail?hour={hour_24}",
                    "hx-target": "#time-detail",
                    "hx-swap": "innerHTML",
                    "title": f"{percentage}% of timezones in preferred hours"
                },
                air.Div({"class": "time-slot-time"}, time_str),
                air.Div({"class": "time-slot-score"}, f"{percentage}%")
            )
        )
    
    return air.Div(
        # Legend
        air.Div(
            {"class": "grid-legend"},
            air.Div(
                {"class": "legend-item"},
                air.Div({"class": "legend-color green"}),
                air.Span("All timezones in preferred hours")
            ),
            air.Div(
                {"class": "legend-item"},
                air.Div({"class": "legend-color yellow"}),
                air.Span("50%+ timezones in preferred hours")
            ),
            air.Div(
                {"class": "legend-item"},
                air.Div({"class": "legend-color red"}),
                air.Span("Less than 50% in preferred hours")
            )
        ),
        
        # Grid
        air.Div(
            {"class": "grid-container"},
            air.Div(
                {"class": "time-grid"},
                *time_slot_elements
            )
        ),
        
        # Detail area
        air.Div(
            {"id": "time-detail"},
            air.P(
                "Click on any time slot to see details for all timezones.",
                {"style": "text-align: center; color: var(--pico-muted-color); font-style: italic;"}
            )
        )
    )


@app.get("/grid-detail")
async def grid_detail(hour: int = 0):
    """Show detailed time breakdown for a specific hour."""
    timezones = get_session_timezones()
    
    if not timezones:
        return air.Div("No timezones selected.")
    
    # Create a datetime for the selected hour
    base_time = datetime.now(ZoneInfo("UTC")).replace(hour=hour, minute=0, second=0, microsecond=0)
    
    # Format the base time for display
    hour_12 = hour % 12 or 12
    am_pm = "AM" if hour < 12 else "PM"
    time_header = f"{hour_12}:00 {am_pm} UTC"
    
    # Create rows for each timezone
    rows = []
    for tz in timezones:
        local_time = base_time.astimezone(ZoneInfo(tz["id"]))
        local_hour = local_time.hour
        
        # Check if in preferred hours
        preferred_start = tz["preferred_start"]
        preferred_end = tz["preferred_end"]
        
        if preferred_end < preferred_start:
            # Wraps around midnight
            in_hours = local_hour >= preferred_start or local_hour < preferred_end
        else:
            in_hours = preferred_start <= local_hour < preferred_end
        
        # Format local time
        local_hour_12 = local_hour % 12 or 12
        local_am_pm = "AM" if local_hour < 12 else "PM"
        local_time_str = f"{local_hour_12}:00 {local_am_pm}"
        local_date_str = local_time.strftime("%a, %b %d")
        
        status_text = "✓ In preferred hours" if in_hours else "✗ Outside preferred hours"
        row_class = "in-hours" if in_hours else "out-hours"
        
        rows.append(
            air.Div(
                {"class": f"timezone-time-row {row_class}"},
                air.Div(
                    air.Strong(tz["name"]),
                    air.Br(),
                    air.Small(local_date_str)
                ),
                air.Div(
                    air.Strong(local_time_str),
                    air.Br(),
                    air.Small(status_text)
                )
            )
        )
    
    return air.Div(
        {"class": "time-detail"},
        air.Div(
            {"class": "time-detail-header"},
            air.H3(f"Details for {time_header}", {"style": "margin: 0;"}),
            air.Button(
                "Close",
                **{
                    "hx-get": "/grid-detail-close",
                    "hx-target": "#time-detail",
                    "hx-swap": "innerHTML",
                    "class": "secondary outline",
                    "style": "margin: 0;"
                }
            )
        ),
        *rows
    )


@app.get("/grid-detail-close")
async def grid_detail_close():
    """Close the detail view."""
    return air.P(
        "Click on any time slot to see details for all timezones.",
        {"style": "text-align: center; color: var(--pico-muted-color); font-style: italic;"}
    )


@app.get("/converter")
async def converter_view():
    """Placeholder for converter view."""
    return air.Div(
        air.P("🚧 Converter view coming in Step 4!"),
        air.P("This will let you enter a specific time and see conversions across all timezones.")
    )
