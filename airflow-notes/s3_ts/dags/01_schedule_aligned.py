"""
DAG 01 — Schedule-aligned timestamp path
=========================================
Assumption: the upstream system uploads exactly one batch per hour and
the folder timestamp matches the top of each hour, i.e. a batch uploaded
for 14:00 UTC lands at  s3://my-bucket/SOME_PREFIX/20240101140000/*.csv

We schedule the DAG @hourly.  For every run:
  data_interval_start  = 2024-01-01T14:00:00 UTC
  data_interval_end    = 2024-01-01T15:00:00 UTC

Rendering  data_interval_start.strftime('%Y%m%d%H%M%S')  produces
"20240101140000", which is exactly the folder we want.

The S3KeySensor waits until at least one .csv file exists under that
prefix, then downstream processing can use the same rendered prefix.
"""

import pendulum
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

S3_BUCKET = "my-bucket"
S3_PREFIX = "SOME_PREFIX"
AWS_CONN_ID = "aws_default"


def _process_batch(batch_prefix: str) -> None:
    """Placeholder: read CSVs from batch_prefix and do work."""
    print(f"Processing files under s3://{S3_BUCKET}/{batch_prefix}/")
    # real implementation: use S3Hook or boto3 to list & read files


with DAG(
    dag_id="01_schedule_aligned",
    schedule="0 * * * *",  # @hourly
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["s3", "sensor", "schedule-aligned"],
):
    # Jinja renders data_interval_start to the exact hourly folder name.
    # wildcard_match=False → exact key must exist (fastest, no listing needed
    # for the prefix check; Airflow just calls HeadObject on the key).
    # We use a wildcard key so Airflow lists the prefix and finds any .csv.
    wait_for_batch = S3KeySensor(
        task_id="wait_for_batch",
        bucket_name=S3_BUCKET,
        bucket_key=(
            f"{S3_PREFIX}"
            "/{{ data_interval_start.strftime('%Y%m%d%H%M%S') }}"
            "/*.csv"
        ),
        wildcard_match=True,  # needed because of the * in the key
        aws_conn_id=AWS_CONN_ID,
        poke_interval=60,
        timeout=60 * 60,  # give up after 1 h
        mode="reschedule",  # free the worker slot while waiting
    )

    process = PythonOperator(
        task_id="process_batch",
        python_callable=_process_batch,
        op_kwargs={
            # Same Jinja expression resolves to the same path at runtime.
            "batch_prefix": (
                f"{S3_PREFIX}"
                "/{{ data_interval_start.strftime('%Y%m%d%H%M%S') }}"
            ),
        },
    )

    wait_for_batch >> process
