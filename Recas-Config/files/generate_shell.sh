#!/usr/bin/env bash
set -euo pipefail

# ==================================================
# Resolve script location (robust to cwd)
# ==================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ==================================================
# CONFIG
# ==================================================
MAIN_PY="$HOME/Projects/test/src/main.py"
OUT_DIR="$SCRIPT_DIR/jobs/shell"
OUT_SCRIPT="$OUT_DIR/run_pipeline.sh"
CONDA_ENV="$HOME/miniconda3/envs/Thor"

# ==================================================
# HELP
# ==================================================
show_help() {
    cat <<EOF
Usage:
  bash generate_run_no_config.sh

Generate a single executable shell script that runs the main Python script
without requiring a configuration file (script uses hardcoded/default config).

Options:
  -h, --help    Show this help message
EOF
}

# ==================================================
# ARGUMENT PARSING
# ==================================================
if [[ $# -eq 1 && ( "$1" == "-h" || "$1" == "--help" ) ]]; then
    show_help
    exit 0
fi

# ==================================================
# CREATE OUTPUT DIRECTORY
# ==================================================
mkdir -p "$OUT_DIR"
rm -f "$OUT_DIR"/*.sh

echo "[INFO] Generating single executable script..."
echo ""

# ==================================================
# GENERATE EXECUTABLE SCRIPT
# ==================================================
cat > "$OUT_SCRIPT" <<EOF
#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "  Experiment: pipeline (no config)"
echo "  Job ID: \${JOBID:-N/A}"
echo "=========================================="
echo ""

# ===================== ENVIRONMENT =====================
CONDA_ENV="$CONDA_ENV"

if [[ ! -d "\$CONDA_ENV" ]]; then
  echo "ERROR: Conda environment not found: \$CONDA_ENV" >&2
  exit 1
fi

export PATH="\$CONDA_ENV/bin:\$PATH"
export LD_LIBRARY_PATH="\$CONDA_ENV/lib:\$CONDA_ENV/lib64:\${LD_LIBRARY_PATH:-}"
export LIBRARY_PATH="\$CONDA_ENV/lib:\$CONDA_ENV/lib64:\${LIBRARY_PATH:-}"
export CPATH="\$CONDA_ENV/include:\${CPATH:-}"
export PKG_CONFIG_PATH="\$CONDA_ENV/lib/pkgconfig:\${PKG_CONFIG_PATH:-}"
export PYTHONNOUSERSITE=1

PY="\$CONDA_ENV/bin/python3.10"
[[ -x "\$PY" ]] || PY="\$CONDA_ENV/bin/python"

echo "[INFO] Python: \$("\$PY" -c 'import sys; print(sys.version)')"
echo ""

# ===================== EXECUTION =====================
MAIN_PY="$MAIN_PY"

if [[ ! -f "\$MAIN_PY" ]]; then
  echo "ERROR: main code not found: \$MAIN_PY" >&2
  exit 1
fi

echo "[INFO] Running pipeline..."
echo ""

"\$PY" -u "\$MAIN_PY"
EXIT_CODE=\$?

echo ""
echo "=========================================="
if [[ \$EXIT_CODE -eq 0 ]]; then
    echo "  ✓ Pipeline completed successfully"
else
    echo "  ✗ Pipeline failed (exit code: \$EXIT_CODE)"
fi
echo "=========================================="

exit \$EXIT_CODE
EOF

# ==================================================
# MAKE SCRIPT EXECUTABLE
# ==================================================
chmod +x "$OUT_SCRIPT"

echo "[OK] Created executable script: $OUT_SCRIPT"
echo ""
echo "Next steps:"
echo "  bash make_condor_jobs.sh"
echo "  condor_submit jobs/condor/run_pipeline.sub or"
echo "  for f in condor/*.sub; do condor_submit \$f; done"