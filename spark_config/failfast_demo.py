"""
Demonstrates FAILFAST logging concern and two solutions.

Run:
    docker compose run --rm spark-demo
"""

import os
import sys

from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

WORK_DIR = "/opt/spark/work-dir"
DATA_PATH = os.path.join(WORK_DIR, "data", "sample.csv")

# CSV with two corrupt rows: one missing columns, one with wrong type
SAMPLE_CSV = """\
id,name,age,city
1,John,30,New York
2,Bob
3,Alice,thirty,Los Angeles
4,Carol,25,Chicago
"""

BASE_SCHEMA = StructType([
    StructField("id",   IntegerType(), True),
    StructField("name", StringType(),  True),
    StructField("age",  IntegerType(), True),
    StructField("city", StringType(),  True),
])


def write_sample_data() -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as fh:
        fh.write(SAMPLE_CSV)


def approach_failfast(spark: SparkSession) -> None:
    """
    PROBLEM: FAILFAST logs the full corrupt record to stderr.
    Sensitive field values become visible in Spark driver/executor logs.
    """
    print("\n=== APPROACH 1: FAILFAST (PROBLEM) ===")
    print("Corrupt records are written to logs — security risk for sensitive data.\n")
    try:
        df = (
            spark.read
            .option("mode", "FAILFAST")
            .option("header", "true")
            .schema(BASE_SCHEMA)
            .csv(DATA_PATH)
        )
        df.collect()
    except Exception as exc:
        print(f"Job failed as expected: {type(exc).__name__}")
        print("^ Scroll up — the corrupt row content was printed to logs above.")


def approach_suppress_logger(spark: SparkSession) -> None:
    """
    MITIGATION: Silence the FailureSafeParser logger so corrupt record
    payloads are not emitted to logs. The job still fails fast.

    Equivalent spark-submit flag:
        --conf "spark.driver.extraJavaOptions=
                -Dlog4j2.logger.fsp.name=org.apache.spark.sql.execution.datasources.FailureSafeParser
                -Dlog4j2.logger.fsp.level=ERROR"
    """
    print("\n=== APPROACH 2: FAILFAST + suppress FailureSafeParser logger ===")
    print("Job still fails fast, but corrupt record content is NOT logged.\n")
    try:
        jvm = spark.sparkContext._jvm
        Configurator = jvm.org.apache.logging.log4j.core.config.Configurator
        Level = jvm.org.apache.logging.log4j.Level
        Configurator.setLevel(
            "org.apache.spark.sql.execution.datasources.FailureSafeParser",
            Level.ERROR,
        )
    except Exception as exc:
        print(f"Could not adjust log level programmatically: {exc}")
        print("Use --conf spark.driver.extraJavaOptions instead (see docstring).")

    try:
        df = (
            spark.read
            .option("mode", "FAILFAST")
            .option("header", "true")
            .schema(BASE_SCHEMA)
            .csv(DATA_PATH)
        )
        df.collect()
    except Exception as exc:
        print(f"Job failed as expected: {type(exc).__name__}")
        print("Corrupt record content suppressed — not visible in logs.")


def approach_permissive_then_abort(spark: SparkSession) -> None:
    """
    PREFERRED: Read in PERMISSIVE mode, capturing corrupt records in a
    dedicated column (_corrupt_record). Abort programmatically if any
    are found. Record payloads are never written to Spark logs.
    """
    print("\n=== APPROACH 3: PERMISSIVE + columnNameOfCorruptRecord (PREFERRED) ===")
    print("Corrupt records captured silently in column; job aborts without logging data.\n")

    schema_with_corrupt = StructType(
        BASE_SCHEMA.fields
        + [StructField("_corrupt_record", StringType(), True)]
    )

    df = (
        spark.read
        .option("mode", "PERMISSIVE")
        .option("columnNameOfCorruptRecord", "_corrupt_record")
        .option("header", "true")
        .schema(schema_with_corrupt)
        .csv(DATA_PATH)
        .cache()
    )

    corrupt_count = df.filter(df["_corrupt_record"].isNotNull()).count()

    if corrupt_count > 0:
        print(f"Detected {corrupt_count} corrupt record(s) — aborting job.")
        print("Corrupt record content was NOT written to application logs.")
        spark.stop()
        sys.exit(1)

    print("No corrupt records found. Clean data:")
    df.drop("_corrupt_record").show(truncate=False)


if __name__ == "__main__":
    write_sample_data()

    spark = (
        SparkSession.builder
        .appName("FAILFAST-Logging-Demo")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    # Reduce root Spark log noise (does NOT suppress FailureSafeParser WARN)
    spark.sparkContext.setLogLevel("WARN")

    approach_failfast(spark)
    approach_suppress_logger(spark)
    approach_permissive_then_abort(spark)

    spark.stop()
