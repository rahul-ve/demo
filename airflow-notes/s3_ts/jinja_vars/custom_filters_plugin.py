"""
custom_filters_plugin.py
=========================
Drop this file into your Airflow  plugins/  directory.
After a scheduler + webserver restart the filters are available globally
in ALL DAGs — no per-DAG configuration required.

Usage in any DAG's template fields:
    {{ data_interval_start | ts_compact }}
    {{ data_interval_start | ds_slash }}
    {{ data_interval_start | ts_hour_bucket }}

Verify the plugin loaded:
    airflow plugins list
"""

from airflow.plugins_manager import AirflowPlugin


# ---------------------------------------------------------------------------
# Custom filter callables
# ---------------------------------------------------------------------------

def ts_compact(dt) -> str:
    """
    YYYYMMDDHHmmss — no T separator.
    Matches the S3 folder convention:  SOME_PREFIX/20240101143022/
    Jinja equivalent without this filter: {{ dt | ts_nodash | replace('T','') }}
    """
    return dt.strftime("%Y%m%d%H%M%S")


def ds_slash(dt) -> str:
    """
    YYYY/MM/DD — Hive-style date partition.
    Useful for  s3://bucket/prefix/2024/01/01/  paths.
    """
    return dt.strftime("%Y/%m/%d")


def ts_hour_bucket(dt) -> str:
    """
    YYYYMMDDhh — hour-level bucket, ignores minutes and seconds.
    """
    return dt.strftime("%Y%m%d%H")


def yyyyww(dt) -> str:
    """
    YYYYww — ISO year + zero-padded week number.
    Useful for weekly S3 partitions.
    """
    return dt.strftime("%G%V")


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------
class CustomDateFiltersPlugin(AirflowPlugin):
    name = "custom_date_filters"

    # Keys become the filter names used in {{ value | key }} expressions.
    user_defined_filters = {
        "ts_compact": ts_compact,
        "ds_slash": ds_slash,
        "ts_hour_bucket": ts_hour_bucket,
        "yyyyww": yyyyww,
    }
