# Clearwater PD Active Calls Tracker

Automated tracking and analysis of Clearwater Police Department active calls for service.

## What This Does

This tool automatically fetches data from the [CPD Active Calls page](https://apps.myclearwater.com/activecalls/) every 5 minutes and:

- **Logs all activity** - New calls and resolved calls are recorded
- **Tracks patterns** - Call types, locations, times, and frequency
- **Archives everything** - Daily JSON archives for historical analysis
- **Runs 24/7** - GitHub Actions handles scheduling, no server needed

## Data Collected

| Field | Description |
|-------|-------------|
| `Online_Description` | Type of call (Traffic Stop, Disturbance, etc.) |
| `Master_Incident_Number` | Unique incident ID |
| `Address` | Location of the call |
| `Response_Date` | When the call was dispatched |

## Metrics Tracked

### Real-Time
- Total active calls at each snapshot
- New calls since last check
- Resolved calls since last check

### Historical Analysis
- **Call Type Distribution** - What kinds of calls dominate?
- **Geographic Hotspots** - Which addresses get repeated attention?
- **Hourly Patterns** - When is CPD busiest?
- **Resolution Times** - How long do calls stay active?
- **Peak Activity** - Maximum concurrent calls observed

## File Structure

```
├── data/
│   ├── current_calls.json    # Latest snapshot
│   ├── historical_log.txt    # Human-readable activity log
│   └── archive/
│       └── YYYY-MM-DD.json   # Daily archives
├── analysis/
│   └── stats.json            # Running statistics
└── scripts/
    └── fetch_active_calls.py # Main tracking script
```

## Setup Your Own

1. **Fork this repository**

2. **Enable GitHub Actions**
   - Go to Settings → Actions → General
   - Select "Allow all actions"
   - Save

3. **The workflow will start automatically**
   - Runs every 5 minutes
   - First run triggered on push to main

4. **Optional: Add notifications**
   - See `scripts/` for webhook examples
   - Discord, Slack, or email alerts for specific call types

## Why This Matters

Public transparency. The data is already public - this just makes it searchable, analyzable, and permanent. Patterns emerge over time that aren't visible from a single snapshot.

## Legal

All data is sourced from publicly available Clearwater PD active calls page. This tool simply automates what any person could do manually by refreshing the page and taking notes.

## Note on Delay

Per CPD's own disclosure, the active calls data is delayed by approximately 20 minutes from real-time dispatch.

---

*Tracking started: See `analysis/stats.json` for details*
