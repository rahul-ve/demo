"""
custom_filters_dag_level.py
============================
Demonstrates adding custom Jinja filters scoped to a single DAG via
the `user_defined_filters` argument on the DAG constructor.

These filters are ONLY available inside this DAG's template fields.
No restart, no plugin deployment needed — changes take effect immediately
on next DAG parse.

Usage in template fields:
    {{ data_interval_start | ts_compact }}
    {{ data_interval_start | ds_slash }}
    {{ data_interval_start | ts_hour_bucket }}
"""

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG


# ---------------------------------------------------------------------------
# Custom filter callables — plain Python functions.
# They receive a pendulum.DateTime and must return a str.
# ---------------------------------------------------------------------------

def ts_compact(dt) -> str:
    """
    YYYYMMDDHHmmss — no T separator.
    Useful for S3 paths like  SOME_PREFIX/20240101143022/
    Jinja equivalent: {{ dt | ts_nodash | replace('T', '') }}
    """
    return dt.strftime("%Y%m%d%H%M%S")


def ds_slash(dt) -> str:
    """
    YYYY/MM/DD — Hive-style date partition path.
    Useful for S3 paths like  prefix/2024/01/01/
    """
    return dt.strftime("%Y/%m/%d")


def ts_hour_bucket(dt) -> str:
    """
    YYYYMMDDhh — truncated to the hour.
    Useful when batches are bucketed per hour regardless of minute/second.
    """
    return dt.strftime("%Y%m%d%H")


# ---------------------------------------------------------------------------
# DAG — register the filters via user_defined_filters
# ---------------------------------------------------------------------------
with DAG(
    dag_id="custom_filters_dag_level",
    schedule="@hourly",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    # dict: key = filter name used in {{ ... | name }}, value = callable
    user_defined_filters={
        "ts_compact": ts_compact,
        "ds_slash": ds_slash,
        "ts_hour_bucket": ts_hour_bucket,
    },
    tags=["jinja", "custom-filters", "example"],
):
    # Each bash command demonstrates a custom filter in a template field.
    demo = BashOperator(
        task_id="print_custom_filters",
        bash_command=(
            "echo 'ts_compact      : {{ data_interval_start | ts_compact }}' && "
            "echo 'ds_slash        : {{ data_interval_start | ds_slash }}' && "
            "echo 'ts_hour_bucket  : {{ data_interval_start | ts_hour_bucket }}' && "
            # Combining with a built-in Airflow filter is fine too:
            "echo 'ds (built-in)   : {{ data_interval_start | ds }}'"
        ),
    )
