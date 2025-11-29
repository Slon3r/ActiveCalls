#!/usr/bin/env python3
"""
Optional: Discord webhook notifications for CPD call alerts.
Set DISCORD_WEBHOOK_URL as a GitHub secret to enable.

Triggers on:
- High volume (10+ active calls)
- Specific call types you care about
- Specific addresses/areas
"""

import json
import os
import requests
from pathlib import Path

WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# Customize these triggers
ALERT_CALL_TYPES = [
    "TRAFFIC STOP",
    "PEDESTRIAN STOP",
    "SUSPICIOUS PERSON",
    "SUSPICIOUS VEHICLE",
    # Add more call types you want alerts for
]

ALERT_ADDRESSES = [
    # Add specific addresses or partial matches
    # "CLEVELAND ST",
    # "COURT ST",
]

HIGH_VOLUME_THRESHOLD = 10


def send_discord_alert(title, description, color=0x0052A6):
    """Send a Discord webhook message."""
    if not WEBHOOK_URL:
        print("No Discord webhook configured")
        return
    
    payload = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "footer": {"text": "CPD Active Calls Tracker"}
        }]
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"Discord alert sent: {title}")
    except requests.RequestException as e:
        print(f"Failed to send Discord alert: {e}")


def check_alerts(current_calls, new_calls):
    """Check if any alert conditions are met."""
    alerts = []
    
    # High volume alert
    if len(current_calls) >= HIGH_VOLUME_THRESHOLD:
        alerts.append({
            "title": f"🚨 High Activity: {len(current_calls)} Active Calls",
            "description": "CPD is handling an unusually high number of calls.",
            "color": 0xFF0000  # Red
        })
    
    # Specific call type alerts
    for call in new_calls:
        call_type = call.get('Online_Description', '').upper()
        address = call.get('Address', '')
        incident = call.get('Master_Incident_Number', '')
        
        # Check call type triggers
        for alert_type in ALERT_CALL_TYPES:
            if alert_type in call_type:
                alerts.append({
                    "title": f"📍 {call_type}",
                    "description": f"**Location:** {address}\n**Incident:** {incident}",
                    "color": 0xFFA500  # Orange
                })
                break
        
        # Check address triggers
        for alert_addr in ALERT_ADDRESSES:
            if alert_addr.upper() in address.upper():
                alerts.append({
                    "title": f"📍 Activity at Watched Location",
                    "description": f"**Type:** {call_type}\n**Location:** {address}\n**Incident:** {incident}",
                    "color": 0xFFFF00  # Yellow
                })
                break
    
    return alerts


def main():
    """Check for alerts and send notifications."""
    data_dir = Path(__file__).parent.parent / "data"
    current_file = data_dir / "current_calls.json"
    
    if not current_file.exists():
        print("No current calls data found")
        return
    
    with open(current_file, 'r') as f:
        data = json.load(f)
    
    current_calls = data.get('calls', [])
    
    # For new calls, we'd need to compare with previous
    # This simplified version alerts on all current matching calls
    # In production, integrate this into the main fetch script
    
    alerts = check_alerts(current_calls, current_calls)
    
    for alert in alerts[:5]:  # Limit to 5 alerts per run
        send_discord_alert(alert['title'], alert['description'], alert['color'])


if __name__ == "__main__":
    main()
