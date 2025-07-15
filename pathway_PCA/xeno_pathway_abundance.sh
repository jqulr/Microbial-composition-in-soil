#!/bin/bash

# ==============================================================================
# Xenobiotic Pathway Processing Pipeline
#
# Description:
#   This script runs a 3-step pipeline to:
#     1. Normalize and regroup HUMAnN3 KO-level abundance data
#     2. Filter for xenobiotic degradation pathways using a KO→map reference
#     3. Map KEGG pathway IDs to human-readable names
#
# Usage:
#   bash run_xenobiotic_pipeline.sh \
#     --input   <input_pathway_abundance.tsv> \
#     --mapfile <ko_to_xenobiotic_maps.tsv> \
#     --output  <final_named_output.tsv>
#
# Example:
#   bash run_xenobiotic_pipeline.sh \
#     --input /path/to/scbi_1164_xenobiotic_name_pathway_abundance_v2.tsv \
#     --mapfile /path/to/ko_to_xenobiotic_maps.tsv \
#     --output /path/to/final_named_xenobiotic_pathways.tsv
# ==============================================================================

set -e  # Exit on error

# === Parse arguments ===
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --input) INPUT="$2"; shift ;;
        --output) OUTPUT="$2"; shift ;;
        --mapfile) MAPFILE="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [[ -z "$INPUT" || -z "$OUTPUT" || -z "$MAPFILE" ]]; then
    echo "Usage: $0 --input INPUT_FILE --output OUTPUT_FILE --mapfile KO_TO_XENO_MAP"
    exit 1
fi

# Intermediate file paths (can be adjusted or made user-configurable)
RENORM_OUT="/tmp/renorm.tsv"
REGROUP_OUT="/tmp/regroup.tsv"
FILTERED_OUT="/tmp/xenobiotic_filtered.tsv"

echo "[Step 1] Running HUMAnN renorm and regroup..."
humann_renorm_table \
  --input "$INPUT" \
  --units cpm \
  --output "$RENORM_OUT"

humann_regroup_table \
  --input "$RENORM_OUT" \
  --output "$REGROUP_OUT" \
  --groups uniref90_ko

echo "[Step 2] Filtering for xenobiotic pathways..."
python3 /home/juneq/scripts/post_Humann3_scripts/filter_xenobiotics.py \
  --abundance "$REGROUP_OUT" \
  --mapping "$MAPFILE" \
  --output "$FILTERED_OUT"

echo "[Step 3] Mapping KEGG pathway IDs to human-readable names..."
python3 /home/juneq/scripts/post_Humann3_scripts/map2names.py \
  --input "$FILTERED_OUT" \
  --output "$OUTPUT"

echo "Xenobiotic pathway abundance saved at: '$OUTPUT'"
