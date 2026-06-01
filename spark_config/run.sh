#!/usr/bin/env bash
# Usage: ./run.sh [SPARK_VERSION]
# Examples:
#   ./run.sh        # uses default (4.1.2)
#   ./run.sh 3.5.5  # Spark 3.5.5

set -euo pipefail

VERSION="${1:-4.1.2}"
IMAGE="apache/spark:${VERSION}-python3"

echo "Starting spark-demo with image: ${IMAGE}"
SPARK_IMAGE="${IMAGE}" docker compose run --rm spark-demo
