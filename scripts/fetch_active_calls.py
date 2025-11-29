#!/usr/bin/env python3
"""
CPD Active Calls Tracker
Fetches active calls from Clearwater PD API, tracks changes, and logs everything.
Designed to run via GitHub Actions on a schedule.
"""

import json
import os
import requests
from datetime import datetime, timezone
from pathlib import Path

# Configuration
API_URL = "https://apps.myclearwater.com/activecalls/api/ActiveCalls"
DATA_DIR = Path(__file__).parent.parent / "data"
ARCHIVE_DIR = DATA_DIR / "archive"
ANALYSIS_DIR = Path(__file__).parent.parent / "analysis"

# File paths
CURRENT_CALLS_FILE = DATA_DIR / "current_calls.json"
HISTORICAL_LOG_FILE = DATA_DIR / "historical_log.txt"
STATS_FILE = ANALYSIS_DIR / "stats.json"


def fetch_active_calls():
    """Fetch current active calls from CPD API."""
    try:
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Handle both direct array and wrapped response
        if isinstance(data, dict) and 'data' in data:
            calls = data['data']
        elif isinstance(data, list):
            calls = data
        else:
            calls = []
            
        return calls
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


def load_previous_calls():
    """Load the previous snapshot of calls."""
    if CURRENT_CALLS_FILE.exists():
        with open(CURRENT_CALLS_FILE, 'r') as f:
            return json.load(f)
    return {"calls": [], "timestamp": None}


def save_current_calls(calls, timestamp):
    """Save current calls snapshot."""
    data = {
        "calls": calls,
        "timestamp": timestamp,
        "count": len(calls)
    }
    with open(CURRENT_CALLS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def parse_response_date(response_date_str):
    """Parse the ISO format date from the API."""
    try:
        # Format: "2024-01-15T14:30:00"
        return datetime.fromisoformat(response_date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def compare_calls(previous_calls, current_calls):
    """Compare previous and current calls to find new and resolved incidents."""
    prev_ids = {call.get('Master_Incident_Number') for call in previous_calls}
    curr_ids = {call.get('Master_Incident_Number') for call in current_calls}
    
    new_ids = curr_ids - prev_ids
    resolved_ids = prev_ids - curr_ids
    
    new_calls = [c for c in current_calls if c.get('Master_Incident_Number') in new_ids]
    resolved_calls = [c for c in previous_calls if c.get('Master_Incident_Number') in resolved_ids]
    
    return new_calls, resolved_calls


def format_call_for_log(call, status):
    """Format a call for the human-readable log."""
    incident_num = call.get('Master_Incident_Number', 'UNKNOWN')
    description = call.get('Online_Description', 'Unknown Call Type')
    address = call.get('Address', 'Unknown Location')
    response_date = call.get('Response_Date', '')
    
    # Parse and format the response time
    parsed_time = parse_response_date(response_date)
    time_str = parsed_time.strftime('%I:%M %p') if parsed_time else 'Unknown Time'
    
    return f"[{status}] {incident_num} | {description} | {address} | Response: {time_str}"


def append_to_log(timestamp, new_calls, resolved_calls, total_active):
    """Append changes to the historical log file."""
    with open(HISTORICAL_LOG_FILE, 'a') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"TIMESTAMP: {timestamp}\n")
        f.write(f"TOTAL ACTIVE CALLS: {total_active}\n")
        f.write(f"{'='*80}\n")
        
        if new_calls:
            f.write(f"\n--- NEW CALLS ({len(new_calls)}) ---\n")
            for call in new_calls:
                f.write(format_call_for_log(call, "NEW") + "\n")
        
        if resolved_calls:
            f.write(f"\n--- RESOLVED CALLS ({len(resolved_calls)}) ---\n")
            for call in resolved_calls:
                f.write(format_call_for_log(call, "RESOLVED") + "\n")
        
        if not new_calls and not resolved_calls:
            f.write("\nNo changes since last check.\n")


def archive_daily_data(calls, timestamp):
    """Archive data to daily JSON file."""
    date_str = datetime.now().strftime('%Y-%m-%d')
    archive_file = ARCHIVE_DIR / f"{date_str}.json"
    
    # Load existing archive or create new
    if archive_file.exists():
        with open(archive_file, 'r') as f:
            archive_data = json.load(f)
    else:
        archive_data = {"date": date_str, "snapshots": []}
    
    # Add current snapshot
    archive_data["snapshots"].append({
        "timestamp": timestamp,
        "call_count": len(calls),
        "calls": calls
    })
    
    with open(archive_file, 'w') as f:
        json.dump(archive_data, f, indent=2)


def update_stats(new_calls, resolved_calls, total_active):
    """Update running statistics."""
    if STATS_FILE.exists():
        with open(STATS_FILE, 'r') as f:
            stats = json.load(f)
    else:
        stats = {
            "total_calls_tracked": 0,
            "total_resolved": 0,
            "call_types": {},
            "addresses": {},
            "hourly_distribution": {str(i): 0 for i in range(24)},
            "first_tracked": None,
            "last_updated": None,
            "peak_active_calls": 0,
            "total_snapshots": 0
        }
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Update basic counts
    stats["total_calls_tracked"] += len(new_calls)
    stats["total_resolved"] += len(resolved_calls)
    stats["last_updated"] = timestamp
    stats["total_snapshots"] += 1
    
    if stats["first_tracked"] is None:
        stats["first_tracked"] = timestamp
    
    if total_active > stats["peak_active_calls"]:
        stats["peak_active_calls"] = total_active
    
    # Track call types
    for call in new_calls:
        call_type = call.get('Online_Description', 'Unknown')
        stats["call_types"][call_type] = stats["call_types"].get(call_type, 0) + 1
        
        # Track addresses
        address = call.get('Address', 'Unknown')
        stats["addresses"][address] = stats["addresses"].get(address, 0) + 1
        
        # Track hourly distribution
        response_date = call.get('Response_Date', '')
        parsed_time = parse_response_date(response_date)
        if parsed_time:
            hour = str(parsed_time.hour)
            stats["hourly_distribution"][hour] = stats["hourly_distribution"].get(hour, 0) + 1
    
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    
    return stats


def generate_summary(stats):
    """Generate a summary for the README or output."""
    top_call_types = sorted(stats["call_types"].items(), key=lambda x: x[1], reverse=True)[:10]
    top_addresses = sorted(stats["addresses"].items(), key=lambda x: x[1], reverse=True)[:10]
    
    summary = []
    summary.append("## CPD Active Calls Tracker - Statistics\n")
    summary.append(f"**Last Updated:** {stats['last_updated']}\n")
    summary.append(f"**Tracking Since:** {stats['first_tracked']}\n")
    summary.append(f"**Total Snapshots:** {stats['total_snapshots']}\n")
    summary.append(f"**Total Calls Tracked:** {stats['total_calls_tracked']}\n")
    summary.append(f"**Total Resolved:** {stats['total_resolved']}\n")
    summary.append(f"**Peak Active Calls:** {stats['peak_active_calls']}\n")
    
    summary.append("\n### Top 10 Call Types\n")
    for call_type, count in top_call_types:
        summary.append(f"- {call_type}: {count}\n")
    
    summary.append("\n### Top 10 Addresses\n")
    for address, count in top_addresses:
        summary.append(f"- {address}: {count}\n")
    
    return "".join(summary)


def main():
    """Main execution function."""
    print(f"CPD Active Calls Tracker - {datetime.now(timezone.utc).isoformat()}")
    print("-" * 60)
    
    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize log file if it doesn't exist
    if not HISTORICAL_LOG_FILE.exists():
        with open(HISTORICAL_LOG_FILE, 'w') as f:
            f.write("CLEARWATER PD ACTIVE CALLS - HISTORICAL LOG\n")
            f.write(f"Tracking started: {datetime.now(timezone.utc).isoformat()}\n")
            f.write("=" * 80 + "\n")
    
    # Fetch current data
    current_calls = fetch_active_calls()
    
    if current_calls is None:
        print("Failed to fetch data. Exiting.")
        return 1
    
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"Fetched {len(current_calls)} active calls")
    
    # Load previous data
    previous_data = load_previous_calls()
    previous_calls = previous_data.get("calls", [])
    
    # Compare
    new_calls, resolved_calls = compare_calls(previous_calls, current_calls)
    print(f"New calls: {len(new_calls)}")
    print(f"Resolved calls: {len(resolved_calls)}")
    
    # Log changes
    append_to_log(timestamp, new_calls, resolved_calls, len(current_calls))
    
    # Save current state
    save_current_calls(current_calls, timestamp)
    
    # Archive
    archive_daily_data(current_calls, timestamp)
    
    # Update stats
    stats = update_stats(new_calls, resolved_calls, len(current_calls))
    
    # Print summary
    print("\n" + generate_summary(stats))
    
    # Set GitHub Actions output if running in CI
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"total_active={len(current_calls)}\n")
            f.write(f"new_calls={len(new_calls)}\n")
            f.write(f"resolved_calls={len(resolved_calls)}\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
