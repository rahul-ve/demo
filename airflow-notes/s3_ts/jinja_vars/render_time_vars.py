"""
render_time_vars.py
====================
Run directly with:  python render_time_vars.py [YYYY-MM-DDTHH:MM:SS[+HH:MM]]

Simulates every time-related Airflow Jinja variable and filter for a given
logical_date / data_interval_start without needing a running Airflow instance.

Reference: https://airflow.apache.org/docs/apache-airflow/2.11.2/templates-ref.html
"""

import sys
import pendulum

# ---------------------------------------------------------------------------
# Parse optional date argument, fall back to a sensible demo value
# ---------------------------------------------------------------------------
if len(sys.argv) > 1:
    dt = pendulum.parse(sys.argv[1])
else:
    dt = pendulum.datetime(2024, 1, 1, 14, 30, 22, tz="UTC")

# For @daily schedule: interval_start = logical_date, interval_end = +1 day
data_interval_start = dt
data_interval_end = dt.add(days=1)

print(f"Simulating logical_date = {dt.isoformat()}")
print(f"             schedule   = @daily  (adjust data_interval_end below for other schedules)")
print()

# ---------------------------------------------------------------------------
# Top-level shortcut variables (pre-rendered strings in Airflow context)
# ---------------------------------------------------------------------------
print("=" * 60)
print("TOP-LEVEL STRING SHORTCUTS  ({{ ds }}, {{ ts }}, ...)")
print("=" * 60)

# {{ ds }} — same as {{ logical_date | ds }}
ds = dt.to_date_string()                     # "2024-01-01"
print(f"  {{{{ ds }}}}                    = {ds}")

# {{ ds_nodash }} — same as {{ logical_date | ds_nodash }}
ds_nodash = dt.format("YYYYMMDD")            # "20240101"
print(f"  {{{{ ds_nodash }}}}             = {ds_nodash}")

# {{ ts }} — same as {{ logical_date | ts }}
ts = dt.isoformat()                          # "2024-01-01T14:30:22+00:00"
print(f"  {{{{ ts }}}}                    = {ts}")

# {{ ts_nodash }} — same as {{ logical_date | ts_nodash }}
ts_nodash = dt.format("YYYYMMDDTHHmmss")     # "20240101T143022"
print(f"  {{{{ ts_nodash }}}}             = {ts_nodash}")

# {{ ts_nodash_with_tz }} — same as {{ logical_date | ts_nodash_with_tz }}
ts_nodash_with_tz = dt.format("YYYYMMDDTHHmmssZZ")  # "20240101T143022+0000"
print(f"  {{{{ ts_nodash_with_tz }}}}     = {ts_nodash_with_tz}")

print()

# ---------------------------------------------------------------------------
# pendulum.DateTime context objects
# ---------------------------------------------------------------------------
print("=" * 60)
print("PENDULUM DATETIME OBJECTS  (support .strftime, .add, .subtract, ...)")
print("=" * 60)

print(f"  {{{{ logical_date }}}}          = {dt}")
print(f"  {{{{ data_interval_start }}}}   = {data_interval_start}")
print(f"  {{{{ data_interval_end }}}}     = {data_interval_end}")

print()

# ---------------------------------------------------------------------------
# Jinja filters applied to pendulum objects
# ---------------------------------------------------------------------------
print("=" * 60)
print("JINJA FILTERS  ({{ <var> | <filter> }})")
print("=" * 60)

filters = [
    ("ds",              dt.to_date_string(),           "YYYY-MM-DD"),
    ("ds_nodash",       dt.format("YYYYMMDD"),         "YYYYMMDD"),
    ("ts",              dt.isoformat(),                "ISO 8601 with tz"),
    ("ts_nodash",       dt.format("YYYYMMDDTHHmmss"),  "YYYYMMDDTHHmmss"),
    ("ts_nodash_with_tz", dt.format("YYYYMMDDTHHmmssZZ"), "YYYYMMDDTHHmmssZZ"),
]
for name, value, description in filters:
    print(f"  {{{{ logical_date | {name:<20} }}}} = {value:<30}  # {description}")

print()

# ---------------------------------------------------------------------------
# strftime patterns — what you actually need for S3 timestamp paths
# ---------------------------------------------------------------------------
print("=" * 60)
print("strftime PATTERNS ON PENDULUM OBJECTS  (most useful for S3 paths)")
print("=" * 60)

strftime_examples = [
    ("%Y%m%d%H%M%S",   "YYYYMMDDHHMMSS  ← S3 folder, no T separator"),
    ("%Y%m%d",         "YYYYMMDD        ← date wildcard prefix"),
    ("%Y/%m/%d",       "YYYY/MM/DD      ← Hive-style S3 partition"),
    ("%Y-%m-%d",       "YYYY-MM-DD      ← same as | ds filter"),
    ("%H%M%S",         "HHMMSS          ← time portion only"),
    ("%Y%m%d%H",       "YYYYMMDDHH      ← hourly partition prefix"),
]
for fmt, note in strftime_examples:
    print(f"  {{{{ data_interval_start.strftime('{fmt}') }}}}  →  {dt.strftime(fmt):<20}  # {note}")

print()

# ---------------------------------------------------------------------------
# Getting YYYYMMDDHHMMSS without T — the two approaches
# ---------------------------------------------------------------------------
print("=" * 60)
print("GETTING YYYYMMDDHHmmss WITHOUT 'T'  (two approaches)")
print("=" * 60)

# Approach 1: strftime (recommended)
approach1 = dt.strftime('%Y%m%d%H%M%S')
print(f"  Approach 1 — strftime (recommended):")
print(f"    {{{{ data_interval_start.strftime('%Y%m%d%H%M%S') }}}}")
print(f"    → {approach1}")
print()

# Approach 2: ts_nodash filter + replace
approach2 = dt.format("YYYYMMDDTHHmmss").replace("T", "")
print(f"  Approach 2 — ts_nodash filter + Jinja replace:")
print(f"    {{{{ data_interval_start | ts_nodash | replace('T', '') }}}}")
print(f"    → {approach2}")

print()

# ---------------------------------------------------------------------------
# macros equivalents
# ---------------------------------------------------------------------------
print("=" * 60)
print("MACROS  ({{ macros.<name>(...) }})")
print("=" * 60)

ds_str = dt.to_date_string()
print(f"  {{{{ macros.ds_add(ds, 1) }}}}                    = {dt.add(days=1).to_date_string()}")
print(f"  {{{{ macros.ds_add(ds, -1) }}}}                   = {dt.subtract(days=1).to_date_string()}")
print(f"  {{{{ macros.ds_format(ds, '%Y-%m-%d', '%d/%m/%Y') }}}} = {dt.strftime('%d/%m/%Y')}")
print(f"  {{{{ macros.datetime(2024, 1, 1) }}}}             = {pendulum.datetime(2024, 1, 1)}")

print()

# ---------------------------------------------------------------------------
# prev_* / next_* (simulated, Airflow computes these from DAG run history)
# ---------------------------------------------------------------------------
print("=" * 60)
print("PREV / NEXT  (computed by Airflow from run history; simulated here)")
print("=" * 60)

prev_start = data_interval_start.subtract(days=1)
prev_end   = data_interval_start
next_start = data_interval_end
next_end   = data_interval_end.add(days=1)

print(f"  {{{{ prev_data_interval_start_success }}}} = {prev_start}  (simulated)")
print(f"  {{{{ prev_data_interval_end_success }}}}   = {prev_end}  (simulated)")
print(f"  next interval start                    = {next_start}  (simulated)")
print(f"  next interval end                      = {next_end}  (simulated)")

print()

# ---------------------------------------------------------------------------
# Deprecated vars (kept for reference, avoid in new DAGs)
# ---------------------------------------------------------------------------
print("=" * 60)
print("DEPRECATED  (backward-compat only — do not use in new DAGs)")
print("=" * 60)

print(f"  {{{{ execution_date }}}}        = {dt}  (use logical_date)")
print(f"  {{{{ yesterday_ds }}}}          = {dt.subtract(days=1).to_date_string()}  (use macros.ds_add(ds, -1))")
print(f"  {{{{ tomorrow_ds }}}}           = {dt.add(days=1).to_date_string()}  (use macros.ds_add(ds, 1))")
print(f"  {{{{ next_execution_date }}}}   = {data_interval_end}  (use data_interval_end)")
print(f"  {{{{ prev_execution_date }}}}   = {prev_start}  (use prev_data_interval_start_success)")

print()
print("Done. Pass a datetime as argument to use a different base date:")
print("  python render_time_vars.py 2024-06-15T08:00:00+00:00")
