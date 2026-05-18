"""
DAG 04 — Discover and process all unprocessed batches
=======================================================
Rather than having the DAG try to predict which timestamp folder will
arrive, this approach inverts the logic:

  1. A broad S3KeySensor fires when ANY new .csv lands under SOME_PREFIX/.
  2. A Python task lists ALL timestamp sub-prefixes under SOME_PREFIX/.
  3. It compares them against a simple "already processed" registry
     (here: an S3 marker file per batch; use a DB table in production).
  4. It returns a list of unprocessed batch prefixes via XCom.
  5. A dynamic task mapping fans out one process task per unprocessed batch.

This is the most resilient approach when:
  • Batch arrival frequency is irregular or can change.
  • Multiple batches can arrive within one schedule interval.
  • You want idempotent reprocessing without relying on Airflow run dates.

Dynamic task mapping (Airflow 2.3+) is used to process each discovered
batch in parallel within a single DAG run.
"""

import pendulum
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

S3_BUCKET = "my-bucket"
S3_PREFIX = "SOME_PREFIX"
PROCESSED_MARKER = "_PROCESSED"   # written to batch folder after processing
AWS_CONN_ID = "aws_default"


def _find_unprocessed_batches() -> list[dict]:
    """
    List all timestamp sub-prefixes under SOME_PREFIX/ and return those
    that do NOT yet have a _PROCESSED marker file.
    Returns a list of dicts so dynamic mapping can unpack op_kwargs directly.
    """
    hook = S3Hook(aws_conn_id=AWS_CONN_ID)

    # list_prefixes returns virtual "directories" one level deep:
    # ["SOME_PREFIX/20240101143022/", "SOME_PREFIX/20240102091500/", ...]
    all_prefixes = hook.list_prefixes(
        bucket_name=S3_BUCKET,
        prefix=f"{S3_PREFIX}/",
        delimiter="/",
    ) or []

    unprocessed = []
    for prefix in all_prefixes:
        marker_key = f"{prefix.rstrip('/')}/{PROCESSED_MARKER}"
        if not hook.check_for_key(marker_key, bucket_name=S3_BUCKET):
            # Strip trailing slash so downstream tasks get a clean prefix.
            unprocessed.append({"batch_prefix": prefix.rstrip("/")})

    print(f"Unprocessed batches: {[d['batch_prefix'] for d in unprocessed]}")
    return unprocessed  # list of dicts → feeds dynamic map


def _process_batch(batch_prefix: str) -> None:
    """
    Process all CSVs in the batch and write the _PROCESSED marker.
    Idempotent: if re-run, the marker check in the discovery task
    prevents re-queuing; but even if this task runs twice for the same
    prefix it just overwrites the marker.
    """
    hook = S3Hook(aws_conn_id=AWS_CONN_ID)

    csv_keys = hook.list_keys(
        bucket_name=S3_BUCKET,
        prefix=f"{batch_prefix}/",
        # exclude any marker files from the work list
    ) or []
    csv_keys = [k for k in csv_keys if k.endswith(".csv")]

    print(f"Processing {len(csv_keys)} CSV(s) under s3://{S3_BUCKET}/{batch_prefix}/")
    for key in csv_keys:
        print(f"  → {key}")
        # real work here: read CSV, transform, load, etc.

    # Write marker so future runs skip this batch.
    hook.load_string(
        string_data="",
        key=f"{batch_prefix}/{PROCESSED_MARKER}",
        bucket_name=S3_BUCKET,
        replace=True,
    )
    print(f"Marked {batch_prefix} as processed.")


with DAG(
    dag_id="04_discover_latest",
    schedule="@hourly",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["s3", "sensor", "dynamic-mapping", "discovery"],
):
    # Broad sensor: fires as soon as any .csv exists anywhere under the prefix.
    # This prevents the rest of the DAG running when there is nothing to do.
    wait_for_any_file = S3KeySensor(
        task_id="wait_for_any_file",
        bucket_name=S3_BUCKET,
        bucket_key=f"{S3_PREFIX}/*/*.csv",
        wildcard_match=True,
        aws_conn_id=AWS_CONN_ID,
        poke_interval=2 * 60,
        timeout=6 * 60 * 60,
        mode="reschedule",
    )

    # Discover which batches still need processing.
    discover = PythonOperator(
        task_id="find_unprocessed_batches",
        python_callable=_find_unprocessed_batches,
    )

    # Dynamically map one task instance per unprocessed batch.
    # expand_kwargs unpacks each dict from the returned list as op_kwargs.
    process = PythonOperator.partial(
        task_id="process_batch",
        python_callable=_process_batch,
    ).expand_kwargs(
        discover.output  # XCom from discover task: list[dict]
    )

    wait_for_any_file >> discover >> process
