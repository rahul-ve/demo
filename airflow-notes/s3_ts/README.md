# S3 Timestamp-Prefix Batch Processing Patterns

Files land in S3 with the structure:

```
s3://my-bucket/SOME_PREFIX/YYYYMMDDHHMMSS/*.csv
```

Each folder name is the upload timestamp of the batch, making it the natural
unique identifier.  The four DAGs here cover progressively less predictable
arrival patterns.

---

## How Airflow context variables resolve to a folder name

Airflow's Jinja runtime exposes `data_interval_start` and `data_interval_end`
as `pendulum.DateTime` objects.  Calling `.strftime(...)` on them inside a
template expression produces the formatted string at render time (just before
the task runs).

| Jinja expression | Resolves to | Notes |
|---|---|---|
| `{{ data_interval_start.strftime('%Y%m%d%H%M%S') }}` | `20240101140000` | Full timestamp — matches an exact folder |
| `{{ data_interval_start.strftime('%Y%m%d') }}` | `20240101` | Date only — needs a wildcard for the time portion |
| `{{ params.batch_ts }}` | whatever the caller passes | Manual / event-driven trigger |
| `{{ logical_date \| ds }}` | `2024-01-01` | ISO date string — not directly usable as folder prefix |

`S3KeySensor` accepts a `wildcard_match=True` flag which applies Python
`fnmatch` patterns to the list of S3 keys, so `*` matches any characters
within a path segment.

---

## DAG 01 — Schedule-aligned (`01_schedule_aligned.py`)

**When to use:** The upstream system uploads exactly one batch per schedule
interval and the folder timestamp equals the top of that interval (e.g.
batch for 14:00 always lands in `YYYYMMDD140000/`).

**How it works:**

```
data_interval_start = 2024-01-01T14:00:00 UTC
  └─ strftime('%Y%m%d%H%M%S') → "20240101140000"

S3KeySensor waits for:
  SOME_PREFIX/20240101140000/*.csv   ← exact prefix, no ambiguity
```

**Pros:**
- Deterministic — no ambiguity about which folder to read.
- Sensor is fast (HeadObject-level check once key exists).
- Built-in catchup handles historical backfilling automatically.

**Cons:**
- Breaks if the upstream system is even slightly late or early, or changes
  its timestamp rounding convention.
- Only one batch per interval is modelled.

---

## DAG 02 — Date-prefix wildcard (`02_date_wildcard.py`)

**When to use:** One batch per day, but it arrives at an unpredictable time
within the day (e.g. after a nightly ETL that varies ±2 hours).

**How it works:**

```
data_interval_start = 2024-01-01T00:00:00 UTC
  └─ strftime('%Y%m%d') → "20240101"

S3KeySensor waits for (wildcard_match=True):
  SOME_PREFIX/20240101*/*.csv
  ↕ fnmatch against all S3 keys
  SOME_PREFIX/20240101143022/orders.csv  ✓  matches

After sensor fires, a resolve_batch_prefix task calls list_prefixes to
get the exact folder, then passes it downstream via XCom.
```

**Pros:**
- Tolerates any arrival time within the scheduled day.
- Still anchored to the DAG schedule — no external input needed.

**Cons:**
- If two batches land within the same schedule interval the sensor fires on
  the first one; the second batch is silently ignored unless you add extra
  logic.  Mitigate by tightening the schedule to match the expected batch
  frequency — e.g. `@hourly` instead of `@daily` if at most one batch lands
  per hour.
- `list_prefixes` after the sensor adds a small extra API call.

---

## DAG 03 — Params-driven manual trigger (`03_params_manual.py`)

**When to use:**
- Reprocessing a specific historical batch.
- Backfilling individual failures without re-running a full date range.
- The DAG is triggered from an external event (Lambda, CI/CD pipeline, etc.)
  that already knows the exact timestamp.

**How it works:**

The DAG has no automatic schedule (`schedule=None`).  A caller triggers it
via the Airflow UI or REST API and supplies:

```json
{ "conf": { "batch_ts": "20240101143022" } }
```

Inside templates, `{{ params.batch_ts }}` resolves to `"20240101143022"`, so:

```
S3KeySensor waits for:
  SOME_PREFIX/20240101143022/*.csv   ← exact folder from the caller
```

The `Param` declaration enforces a 14-digit pattern at trigger time, so a
typo like `"2024-01-01"` is rejected before the DAG even starts.

**Pros:**
- Maximum flexibility — any batch, any time, any reprocessing scenario.
- Validated input: bad `batch_ts` fails fast at trigger, not mid-run.

**Cons:**
- Requires a human or external system to know and supply the timestamp.
- No automatic scheduling → not suitable for continuous ingestion.

**REST API trigger example:**

```bash
curl -X POST \
  "http://airflow:8080/api/v1/dags/03_params_manual/dagRuns" \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d '{"conf": {"batch_ts": "20240101143022"}}'
```

---

## DAG 04 — Discover and process all unprocessed batches (`04_discover_latest.py`)

**When to use:**
- Batch arrival frequency is irregular or can change over time.
- Multiple batches can land within one schedule interval.
- You want fully idempotent processing that is independent of Airflow's
  own run schedule.

**How it works:**

```
Broad sensor:  SOME_PREFIX/*/*.csv  (any file anywhere under prefix)
      │
      ▼  fires when anything arrives
find_unprocessed_batches
  └─ list_prefixes("SOME_PREFIX/")
       → ["SOME_PREFIX/20240101143022/", "SOME_PREFIX/20240102091500/"]
  └─ for each prefix, check_for_key("prefix/_PROCESSED")
       → filter out already-done prefixes
  └─ return [{"batch_prefix": "SOME_PREFIX/20240101143022"},
              {"batch_prefix": "SOME_PREFIX/20240102091500"}]
      │
      ▼  dynamic task map (one task instance per batch)
process_batch (mapped ×2)
  └─ read all CSVs in the batch
  └─ write SOME_PREFIX/<ts>/_PROCESSED marker
```

The `_PROCESSED` marker file is the idempotency mechanism: future runs of
the discovery task skip folders that already have a marker.

**Dynamic task mapping** (Airflow 2.3+): `PythonOperator.partial(...).expand_kwargs(discover.output)` 
creates one mapped task instance per dict in the XCom output, so two
unprocessed batches produce `process_batch[0]` and `process_batch[1]`
running in parallel.

**Pros:**
- Handles variable-frequency batch arrivals automatically.
- Processes multiple batches per run.
- Fully idempotent: safe to rerun, safe after failures.
- No dependency on Airflow run dates matching S3 folder dates.

**Cons:**
- More complex: requires a state mechanism (`_PROCESSED` marker or a DB).
- Dynamic task mapping requires Airflow 2.3+.
- `list_prefixes` scans the entire prefix on every run — can be slow if
  there are thousands of historical folders (mitigate with a date filter
  on the prefix, e.g. `prefix=f"SOME_PREFIX/{today}"`).

---

## Choosing the right pattern

```
Is the batch timestamp predictable from the schedule?
  └─ Yes → DAG 01 (schedule-aligned)

Is it one batch per day, arrival time unknown?
  └─ Yes → DAG 02 (date wildcard)

Do you need to trigger ad-hoc or reprocess a specific batch?
  └─ Yes → DAG 03 (params manual)

Are multiple batches possible per interval, or arrival is irregular?
  └─ Yes → DAG 04 (discover latest)
```

---

## Getting `YYYYMMDDHHmmss` without a `T` separator

The built-in Airflow filters (`ts_nodash`) produce `20240101T143022` — with a
`T` between date and time.  Two ways to get the compact form without `T`:

| Approach | Template expression | Output |
|---|---|---|
| `strftime` (recommended) | `{{ data_interval_start.strftime('%Y%m%d%H%M%S') }}` | `20240101143022` |
| Filter chain | `{{ data_interval_start \| ts_nodash \| replace('T', '') }}` | `20240101143022` |

`strftime` is preferred because the intent is explicit and it avoids a
second rendering pass via the `replace` filter.

---

## Adding custom Jinja filters

### DAG-level — `user_defined_filters` (no restart needed)

Scoped to one DAG. Takes effect on the next DAG parse.

```python
def ts_compact(dt) -> str:
    return dt.strftime("%Y%m%d%H%M%S")   # YYYYMMDDHHmmss, no T

def ds_slash(dt) -> str:
    return dt.strftime("%Y/%m/%d")        # YYYY/MM/DD Hive partition

with DAG(
    dag_id="my_dag",
    user_defined_filters={"ts_compact": ts_compact, "ds_slash": ds_slash},
    ...
):
    BashOperator(
        task_id="demo",
        bash_command="echo {{ data_interval_start | ts_compact }}",
    )
```

See [jinja_vars/custom_filters_dag_level.py](jinja_vars/custom_filters_dag_level.py) for the full example.

### Plugin — global across all DAGs (requires restart)

Drop the file into the Airflow `plugins/` directory.  Restart the scheduler
and webserver once.  Filters are then available in every DAG without any
per-DAG configuration.

```python
# plugins/custom_filters_plugin.py
from airflow.plugins_manager import AirflowPlugin

def ts_compact(dt) -> str:
    return dt.strftime("%Y%m%d%H%M%S")

class CustomDateFiltersPlugin(AirflowPlugin):
    name = "custom_date_filters"
    user_defined_filters = {"ts_compact": ts_compact}
```

Verify it loaded:
```bash
airflow plugins list
```

See [jinja_vars/custom_filters_plugin.py](jinja_vars/custom_filters_plugin.py) for all filters including
`ds_slash`, `ts_hour_bucket`, and `yyyyww`.

### Decision guide

| Need | Use |
|---|---|
| Filter used in one DAG, fast iteration | DAG-level `user_defined_filters` |
| Filter shared across many DAGs | Plugin |
| One-off formatting, no reuse | `strftime` inline in the template |

---

## Debugging Jinja vars without running a DAG

### Option A — Python script (no Airflow needed)

```bash
# default demo date
python jinja_vars/render_time_vars.py

# specific date
python jinja_vars/render_time_vars.py 2024-06-15T08:00:00+00:00
```

Prints every context variable, all five built-in filters, `strftime` patterns,
and the two approaches for `YYYYMMDDHHmmss`.

See [jinja_vars/render_time_vars.py](jinja_vars/render_time_vars.py).

### Option B — `airflow tasks render` (requires running Airflow)

Renders all template fields of a task without executing it:

```bash
airflow tasks render <dag_id> <task_id> <logical_date>
# e.g.
airflow tasks render 01_schedule_aligned wait_for_batch 2024-01-01T14:00:00+00:00
```

---

## Prerequisites

Install the Amazon provider:

```bash
pip install apache-airflow-providers-amazon
```

Create an Airflow connection `aws_default` with your AWS credentials, or
configure IAM roles if running on EC2/ECS.
