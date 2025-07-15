#!/bin/bash

# ==============================================================================
# Batch Xenobiotic Pathway Processing Pipeline
#
# Description:
#   This script loops through a directory of KO abundance files and applies
#   the xenobiotic pathway pipeline (renorm → regroup → filter → map2names)
#
# Usage:
#   bash run_xeno_pipeline_batch.sh \
#     --input_dir  <input_directory> \
#     --output_dir <output_directory> \
#     --mapfile    <ko_to_xenobiotic_maps.tsv>
#
# ==============================================================================

set -e

# === Parse arguments ===
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --input_dir) INPUT_DIR="$2"; shift ;;
        --output_dir) OUTPUT_DIR="$2"; shift ;;
        --mapfile) MAPFILE="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [[ -z "$INPUT_DIR" || -z "$OUTPUT_DIR" || -z "$MAPFILE" ]]; then
    echo "Usage: $0 --input_dir INPUT_DIR --output_dir OUTPUT_DIR --mapfile KO_TO_XENO_MAP"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

# === Process each KO input file ===
for input_file in "$INPUT_DIR"/*_merged_genefamilies.tsv; do
    sample=$(basename "$input_file" _merged_genefamilies.tsv)

    echo "Processing sample: $sample"

    renorm_out="/tmp/${sample}_renorm.tsv"
    regroup_out="/tmp/${sample}_regroup.tsv"
    filtered_out="/tmp/${sample}_filtered.tsv"
    final_out="${OUTPUT_DIR}/${sample}_xenobiotic_named.tsv"

    # Step 1: HUMAnN normalization and regrouping
    humann_renorm_table --input "$input_file" --units cpm --output "$renorm_out"
    humann_regroup_table --input "$renorm_out" --output "$regroup_out" --groups uniref90_ko

    # Step 2: Filter xenobiotics
    python3 /home/juneq/scripts/post_Humann3_scripts/filter_xenobiotics.py \
      --abundance "$regroup_out" \
      --mapping "$MAPFILE" \
      --output "$filtered_out"

    # Step 3: Map to human-readable names
    python3 /home/juneq/scripts/post_Humann3_scripts/map2names.py \
      --input "$filtered_out" \
      --output "$final_out"

    echo "Finished: $sample → $final_out"
done

echo "All samples processed"
