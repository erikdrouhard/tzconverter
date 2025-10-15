"""Timezone utilities for the meeting scheduler."""
from datetime import datetime, time
from zoneinfo import ZoneInfo, available_timezones
from typing import List, Dict, Tuple


# Common timezones with their display names
COMMON_TIMEZONES = [
    ("America/New_York", "New York (EST/EDT)"),
    ("America/Chicago", "Chicago (CST/CDT)"),
    ("America/Denver", "Denver (MST/MDT)"),
    ("America/Los_Angeles", "Los Angeles (PST/PDT)"),
    ("America/Phoenix", "Phoenix (MST)"),
    ("America/Anchorage", "Anchorage (AKST/AKDT)"),
    ("Pacific/Honolulu", "Honolulu (HST)"),
    ("America/Toronto", "Toronto (EST/EDT)"),
    ("America/Vancouver", "Vancouver (PST/PDT)"),
    ("America/Mexico_City", "Mexico City (CST/CDT)"),
    ("America/Sao_Paulo", "São Paulo (BRT)"),
    ("America/Buenos_Aires", "Buenos Aires (ART)"),
    ("America/Santiago", "Santiago (CLT)"),
    ("Europe/London", "London (GMT/BST)"),
    ("Europe/Paris", "Paris (CET/CEST)"),
    ("Europe/Berlin", "Berlin (CET/CEST)"),
    ("Europe/Rome", "Rome (CET/CEST)"),
    ("Europe/Madrid", "Madrid (CET/CEST)"),
    ("Europe/Amsterdam", "Amsterdam (CET/CEST)"),
    ("Europe/Brussels", "Brussels (CET/CEST)"),
    ("Europe/Vienna", "Vienna (CET/CEST)"),
    ("Europe/Stockholm", "Stockholm (CET/CEST)"),
    ("Europe/Warsaw", "Warsaw (CET/CEST)"),
    ("Europe/Moscow", "Moscow (MSK)"),
    ("Europe/Istanbul", "Istanbul (TRT)"),
    ("Europe/Athens", "Athens (EET/EEST)"),
    ("Africa/Cairo", "Cairo (EET)"),
    ("Africa/Johannesburg", "Johannesburg (SAST)"),
    ("Africa/Lagos", "Lagos (WAT)"),
    ("Africa/Nairobi", "Nairobi (EAT)"),
    ("Asia/Dubai", "Dubai (GST)"),
    ("Asia/Karachi", "Karachi (PKT)"),
    ("Asia/Kolkata", "Mumbai/Delhi (IST)"),
    ("Asia/Bangkok", "Bangkok (ICT)"),
    ("Asia/Singapore", "Singapore (SGT)"),
    ("Asia/Hong_Kong", "Hong Kong (HKT)"),
    ("Asia/Shanghai", "Shanghai (CST)"),
    ("Asia/Tokyo", "Tokyo (JST)"),
    ("Asia/Seoul", "Seoul (KST)"),
    ("Asia/Taipei", "Taipei (CST)"),
    ("Asia/Jakarta", "Jakarta (WIB)"),
    ("Asia/Manila", "Manila (PST)"),
    ("Australia/Perth", "Perth (AWST)"),
    ("Australia/Adelaide", "Adelaide (ACST/ACDT)"),
    ("Australia/Brisbane", "Brisbane (AEST)"),
    ("Australia/Sydney", "Sydney (AEST/AEDT)"),
    ("Australia/Melbourne", "Melbourne (AEST/AEDT)"),
    ("Pacific/Auckland", "Auckland (NZST/NZDT)"),
    ("Pacific/Fiji", "Fiji (FJT)"),
]


def get_common_timezones() -> List[Tuple[str, str]]:
    """Return list of common timezones as (id, display_name) tuples."""
    return COMMON_TIMEZONES


def get_current_time_in_timezone(tz_id: str) -> datetime:
    """Get current time in specified timezone."""
    return datetime.now(ZoneInfo(tz_id))


def convert_time_to_timezones(
    source_dt: datetime,
    source_tz: str,
    target_timezones: List[str]
) -> Dict[str, datetime]:
    """
    Convert a datetime from source timezone to multiple target timezones.
    
    Args:
        source_dt: Datetime object (naive or aware)
        source_tz: Source timezone ID (e.g., "America/New_York")
        target_timezones: List of target timezone IDs
    
    Returns:
        Dictionary mapping timezone ID to converted datetime
    """
    # Ensure source datetime is aware
    if source_dt.tzinfo is None:
        source_dt = source_dt.replace(tzinfo=ZoneInfo(source_tz))
    
    result = {}
    for tz_id in target_timezones:
        result[tz_id] = source_dt.astimezone(ZoneInfo(tz_id))
    
    return result


def is_time_in_preferred_hours(
    dt: datetime,
    preferred_start: int,
    preferred_end: int
) -> bool:
    """
    Check if a datetime falls within preferred hours.
    
    Args:
        dt: Datetime to check
        preferred_start: Start hour (0-23)
        preferred_end: End hour (0-23)
    
    Returns:
        True if time falls within preferred hours
    """
    hour = dt.hour
    
    # Handle case where end < start (e.g., 22:00 to 06:00)
    if preferred_end < preferred_start:
        return hour >= preferred_start or hour < preferred_end
    else:
        return preferred_start <= hour < preferred_end


def calculate_viability_score(
    dt: datetime,
    timezones_config: List[Dict[str, any]]
) -> Tuple[float, str]:
    """
    Calculate viability score for a given time across multiple timezones.
    
    Args:
        dt: Base datetime (should be timezone-aware)
        timezones_config: List of dicts with keys: id, preferred_start, preferred_end
    
    Returns:
        Tuple of (score 0.0-1.0, color_class)
    """
    if not timezones_config:
        return (0.0, "red")
    
    in_preferred_count = 0
    total_count = len(timezones_config)
    
    for tz_config in timezones_config:
        tz_id = tz_config["id"]
        preferred_start = tz_config.get("preferred_start", 9)
        preferred_end = tz_config.get("preferred_end", 17)
        
        # Convert time to this timezone
        local_dt = dt.astimezone(ZoneInfo(tz_id))
        
        if is_time_in_preferred_hours(local_dt, preferred_start, preferred_end):
            in_preferred_count += 1
    
    score = in_preferred_count / total_count
    
    # Determine color class based on score
    if score == 1.0:
        color_class = "green"
    elif score >= 0.5:
        color_class = "yellow"
    else:
        color_class = "red"
    
    return (score, color_class)


def generate_24hour_slots(base_date: datetime = None) -> List[datetime]:
    """
    Generate 24 hourly time slots for a given date.
    
    Args:
        base_date: Base datetime (defaults to current time in UTC)
    
    Returns:
        List of 24 datetime objects, one for each hour
    """
    if base_date is None:
        base_date = datetime.now(ZoneInfo("UTC"))
    
    # Start at midnight of the base date
    start = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return [start.replace(hour=h) for h in range(24)]


def format_timezone_display(tz_id: str) -> str:
    """Get display name for a timezone ID."""
    for tid, name in COMMON_TIMEZONES:
        if tid == tz_id:
            return name
    return tz_id

