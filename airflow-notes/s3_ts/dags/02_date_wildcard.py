"""
DAG 02 — Date-prefix wildcard sensor
======================================
Assumption: one batch per day, but it arrives at an unpredictable time
(e.g. upstream ETL finishes anywhere between 02:00 and 06:00 UTC).
We therefore cannot predict the full timestamp folder name in advance.

The folder looks like:  SOME_PREFIX/20240101<HHMMSS>/*.csv
We DO know the date portion (20240101), so we use a wildcard on the time.

Pattern passed to the sensor:
  SOME_PREFIX/20240101*/*.csv

S3KeySensor with wildcard_match=True uses fnmatch under the hood:
  fnmatch("SOME_PREFIX/20240101143022/file.csv", "SOME_PREFIX/20240101*/*.csv")
  → True

The sensor fires as soon as the first .csv is visible — it does NOT wait
for the full batch.  If you need the batch to be "complete", pair this with
a second sensor or a manifest file check (see DAG 04 for discovery variant).

CAVEAT: if more than one batch lands on the same calendar day, this sensor
fires on whichever arrives first and does NOT distinguish between them.
"""

import pendulum
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

S3_BUCKET = "my-bucket"
S3_PREFIX = "SOME_PREFIX"
AWS_CONN_ID = "aws_default"


def _resolve_batch_prefix(bucket: str, date_str: str, **context) -> str:
    """
    List S3 keys under SOME_PREFIX/<date_str>* and return the prefix
    of the first batch folder found.  Pushes it to XCom automatically
    via the return value.
    """
    hook = S3Hook(aws_conn_id=AWS_CONN_ID)
    # list_prefixes returns virtual "directories" one level deep
    prefixes = hook.list_prefixes(
        bucket_name=bucket,
        prefix=f"{S3_PREFIX}/{date_str}",
        delimiter="/",
    )
    if not prefixes:
        raise ValueError(f"No batch prefix found for date {date_str}")
    # prefixes looks like ["SOME_PREFIX/20240101143022/"]
    batch_prefix = prefixes[0].rstrip("/")
    print(f"Resolved batch prefix: {batch_prefix}")
    return batch_prefix  # stored in XCom as return value


def _process_batch(batch_prefix: str) -> None:
    print(f"Processing files under s3://{S3_BUCKET}/{batch_prefix}/")


with DAG(
    dag_id="02_date_wildcard",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["s3", "sensor", "wildcard"],
):
    # Sensor uses a wildcard on the time portion of the timestamp folder.
    # data_interval_start.strftime('%Y%m%d') → "20240101"
    wait_for_batch = S3KeySensor(
        task_id="wait_for_batch",
        bucket_name=S3_BUCKET,
        bucket_key=(
            f"{S3_PREFIX}"
            "/{{ data_interval_start.strftime('%Y%m%d') }}"
            "*/*.csv"
        ),
        wildcard_match=True,
        aws_conn_id=AWS_CONN_ID,
        poke_interval=5 * 60,   # check every 5 min
        timeout=8 * 60 * 60,    # give up after 8 h
        mode="reschedule",
    )

    # Once the sensor fires we still need the exact prefix for downstream
    # tasks.  A Python task resolves it via list_prefixes.
    resolve_prefix = PythonOperator(
        task_id="resolve_batch_prefix",
        python_callable=_resolve_batch_prefix,
        op_kwargs={
            "bucket": S3_BUCKET,
            "date_str": "{{ data_interval_start.strftime('%Y%m%d') }}",
        },
    )

    process = PythonOperator(
        task_id="process_batch",
        python_callable=_process_batch,
        op_kwargs={
            # Pull the resolved prefix from XCom.
            "batch_prefix": (
                "{{ task_instance.xcom_pull(task_ids='resolve_batch_prefix') }}"
            ),
        },
    )

    wait_for_batch >> resolve_prefix >> process
