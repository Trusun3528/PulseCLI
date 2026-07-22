import datetime
import httpx
from typing import Any, Dict, List
import icalendar

async def fetch_calendar_events(ics_url: str = "") -> List[Dict[str, Any]]:
    """Fetch calendar events from an ICS URL or default to public holidays if none."""
    if not ics_url:
        return await _fetch_public_holidays()

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(ics_url, timeout=10)
            resp.raise_for_status()
            
            cal = icalendar.Calendar.from_ical(resp.content)
            events = []
            now = datetime.datetime.now(datetime.timezone.utc)
            
            for component in cal.walk():
                if component.name == "VEVENT":
                    start = component.get("dtstart").dt
                    if isinstance(start, datetime.datetime) and start.tzinfo is None:
                        start = start.replace(tzinfo=datetime.timezone.utc)
                    elif isinstance(start, datetime.date) and not isinstance(start, datetime.datetime):
                        start = datetime.datetime.combine(start, datetime.time.min, tzinfo=datetime.timezone.utc)
                        
                    if start >= now:
                        summary = str(component.get("summary", "No Title"))
                        description = str(component.get("description", ""))
                        events.append({
                            "title": summary,
                            "date": start.strftime("%Y-%m-%d %H:%M"),
                            "description": description[:100] + ("..." if len(description) > 100 else ""),
                            "timestamp": start.timestamp()
                        })
            
            events.sort(key=lambda x: x["timestamp"])
            return events[:30]

    except Exception as e:
        return [{"error": str(e)}]

async def _fetch_public_holidays() -> List[Dict[str, Any]]:
    """Fallback to world public holidays if no ICS is provided."""
    url = "https://date.nager.at/api/v3/NextPublicHolidaysWorldwide"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            events = []
            for item in data:
                events.append({
                    "title": f"{item.get('name', '')} ({item.get('countryCode', '')})",
                    "date": item.get('date', ''),
                    "description": "Public Holiday",
                })
            return events[:30]
    except Exception as e:
        return [{"error": f"Failed to fetch holidays: {str(e)}"}]
