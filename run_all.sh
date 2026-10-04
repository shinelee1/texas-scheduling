#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DOCS_FOLDER="${1:-$HOME/data_collection_docx}"

if [[ -n "${ANTHROPIC_API_KEY:-}" && -d "$DOCS_FOLDER" ]]; then
    echo "===== Step 1/3: Code source documents ====="
    python3 code_schedule_docs.py "$DOCS_FOLDER"
else
    echo "===== Step 1/3: Skipping document coding ====="
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        echo "ANTHROPIC_API_KEY is not set; using existing coded_schools.csv."
    fi
    if [[ ! -d "$DOCS_FOLDER" ]]; then
        echo "Documents folder not found: $DOCS_FOLDER; using existing coded_schools.csv."
    fi
fi

echo "===== Step 2/3: Print coverage statistics ====="
python3 summary_stats.py coded_schools.csv

echo "===== Step 3/3: Build charts ====="
python3 make_charts.py coded_schools.csv