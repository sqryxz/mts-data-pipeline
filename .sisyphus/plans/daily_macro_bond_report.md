# Work Plan: Daily Macro & Bond Report Generation

## Objective
Add daily report generation to `main_enhanced.py` that outputs:
1. Macro Indicators with daily values and 7/14/30-day % change
2. Bond Rates yield curve with 7/14/30-day % change

## Requirements

### Output
- **File**: JSON file with daily macro and bond report
- **Time**: 6:00 AM HKT daily (convert to UTC for scheduling)
- **Location**: `data/daily_reports/{date}.json`

### Report Structure

```json
{
  "generated_at": "2026-03-10T06:00:00+08:00",
  "report_date": "2026-03-09",
  "macro_indicators": [
    {
      "indicator": "VIXCLS",
      "name": "CBOE Volatility Index",
      "value": 29.49,
      "change_7d_pct": 5.2,
      "change_14d_pct": 8.7,
      "change_30d_pct": -3.1
    },
    ...
  ],
  "bond_yields": [
    {
      "maturity": "1Y",
      "indicator": "DGS1",
      "yield": 3.59,
      "change_7d_pct": 0.3,
      "change_14d_pct": 0.5,
      "change_30d_pct": 1.2
    },
    ...
  ]
}
```

## Implementation Tasks

### Task 1: Create Report Generation Module
- Create `src/services/daily_report_generator.py`
- Function to fetch latest macro data from database
- Function to calculate percentage changes over 7/14/30 days
- Function to generate yield curve from DGS1-DGS30

### Task 2: Add Scheduling to main_enhanced.py
- Add new task to scheduler for 6 AM HKT
- HKT to UTC: 6 AM HKT = 10 PM UTC (previous day)
- Use existing scheduler infrastructure

### Task 3: Test Report Generation
- Run manually to verify output
- Check calculations are correct
- Verify file output format

## Technical Notes

### Percentage Change Calculation
```
change_pct = ((current_value - past_value) / past_value) * 100
```

### Yield Curve Order
Display in order: 1Y → 2Y → 5Y → 10Y → 20Y → 30Y

### Database Query
- Use existing `CryptoDatabase` class
- Query `macro_indicators` table
- Filter by indicator and date ranges
