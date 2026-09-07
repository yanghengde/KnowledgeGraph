#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$PROJECT_ROOT"

python -m src.graphstudio_sync.cli continuous-publish \
  --job "${GRAPHSYNC_JOB:-camstar-full}" \
  --profile "${GRAPHSYNC_PROFILE:-opcenter2607-core}" \
  --environment "${GRAPHSYNC_ENVIRONMENT:-dev}" \
  --actor "${GRAPHSYNC_ACTOR:-cronjob}" \
  --apply
