"""
DAG 03 — Params-driven manual trigger
=======================================
There is no automatic schedule.  An operator (or CI/CD pipeline) triggers
the DAG manually, supplying the exact batch timestamp as a parameter.

Use cases:
  • Ad-hoc reprocessing of a specific historical batch.
  • Backfilling individual batches that failed.
  • Triggering from an external event system (e.g. Lambda → Airflow REST API).

The caller passes:
  { "conf": { "batch_ts": "20240101143022" } }

via the Airflow UI "Trigger DAG w/ config" dialog or via the REST API:
  POST /api/v1/dags/03_params_manual/dagRuns
  { "conf": { "batch_ts": "20240101143022" } }

Inside the DAG, {{ params.batch_ts }} resolves to "20240101143022" and the
sensor targets  SOME_PREFIX/20240101143022/*.csv  directly.

VALIDATION: Airflow 2.2+ Params support JSON Schema validation, so we
declare the expected format to catch bad inputs at trigger time.
"""

import pendulum
from airflow.models.param import Param
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

S3_BUCKET = "my-bucket"
S3_PREFIX = "SOME_PREFIX"
AWS_CONN_ID = "aws_default"


def _process_batch(batch_prefix: str) -> None:
    print(f"Processing files under s3://{S3_BUCKET}/{batch_prefix}/")


with DAG(
    dag_id="03_params_manual",
    schedule=None,  # manual trigger only
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    params={
        "batch_ts": Param(
            default="20240101000000",
            type="string",
            minLength=14,
            maxLength=14,
            description="Batch timestamp folder name in YYYYMMDDHHMMSS format.",
            # pattern enforced at trigger time — bad value rejected before
            # the DAG even starts running.
            pattern=r"^\d{14}$",
        ),
    },
    tags=["s3", "sensor", "manual", "params"],
):
    wait_for_batch = S3KeySensor(
        task_id="wait_for_batch",
        bucket_name=S3_BUCKET,
        # {{ params.batch_ts }} is rendered from the DAG run conf.
        bucket_key=f"{S3_PREFIX}/{{{{ params.batch_ts }}}}/*.csv",
        wildcard_match=True,
        aws_conn_id=AWS_CONN_ID,
        poke_interval=30,
        timeout=30 * 60,   # shorter timeout — operator knows batch exists
        mode="reschedule",
    )

    process = PythonOperator(
        task_id="process_batch",
        python_callable=_process_batch,
        op_kwargs={
            "batch_prefix": f"{S3_PREFIX}/{{{{ params.batch_ts }}}}",
        },
    )

    wait_for_batch >> process
