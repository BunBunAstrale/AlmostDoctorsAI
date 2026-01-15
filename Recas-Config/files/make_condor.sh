#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash make_condor_jobs.sh [JOBS_DIR] [SUBMIT_DIR] [LOG_DIR]
# Defaults:
JOBS_DIR="${1:-./jobs/shell}"
SUBMIT_DIR="${2:-./jobs/condor}"
LOG_DIR="${3:-./jobs/logs}"

# Resources (can override with: CPUS=32 MEM=40G GPUS=0 bash make_condor_jobs.sh ...)
CPUS="${CPUS:-1}"
MEM="${MEM:-4}"
GPUS="${GPUS:-0}"

mkdir -p "$SUBMIT_DIR" "$LOG_DIR"
rm -f "$SUBMIT_DIR"/*.sub

# Function to get a portable absolute path
to_abs() {
  case "$1" in
    /*) printf "%s\n" "$1" ;;
    *)  (cd "$1" >/dev/null 2>&1 && pwd) ;;
  esac
}

ABS_JOBS_DIR="$(to_abs "$JOBS_DIR")"
ABS_SUBMIT_DIR="$(to_abs "$SUBMIT_DIR")"
ABS_LOG_DIR="$(to_abs "$LOG_DIR")"

shopt -s nullglob
found=0

for exe in "$ABS_JOBS_DIR"/run_*.sh; do
  found=1
  base="$(basename "$exe")"       # e.g.: run_exp1.sh
  name="${base%.sh}"              # e.g.: run_exp1
  sub="$ABS_SUBMIT_DIR/${name}.sub"

  # Ensure the executable has execute permissions
  chmod +x "$exe" || true

  # Exact header required by Condor
  cat > "$sub" <<'STATIC'
universe = vanilla
environment = "JOBID=$(Cluster).$(Process)"
STATIC

  # Rest of the submit file with absolute paths
  cat >> "$sub" <<EOF
getenv = True
should_transfer_files = NO

executable = $exe

log    = $ABS_LOG_DIR/${name}.log
output = $ABS_LOG_DIR/${name}.out
error  = $ABS_LOG_DIR/${name}.err

request_cpus   = $CPUS
request_memory = $MEM
request_gpus   = $GPUS

queue
EOF

  echo "Created submit file: $sub"
done

if [[ "$found" -eq 0 ]]; then
  echo "No executable scripts found in: $ABS_JOBS_DIR (expected: run_*.sh)"
  exit 0
fi

echo "Submit files directory: $ABS_SUBMIT_DIR"
echo "Log files directory   : $ABS_LOG_DIR"
