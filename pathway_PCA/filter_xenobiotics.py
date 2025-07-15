#!/usr/bin/env python3
"""
filter_and_map_ko.py

Description:
    1. Reads a raw KO abundance file where each row has a “gene family” string
       (e.g. “K00003|g__Genus.s__Species”) and an abundance value.
    2. Extracts only the KO identifier (e.g. “K00003”) and its abundance into a clean
       two-column table.
    3. Loads a KO→xenobiotic mapping file (with columns “KO” and “Map”).
    4. Filters the cleaned KO abundances to those present in the mapping.
    5. Merges on the mapping, placing “Map” immediately after “KO”, then the abundance.
    6. Writes out the final combined TSV.

Usage:
    > python /home/juneq/scripts/post_Humann3_scripts/filter_xenobiotics.py \
        --abundance /home/juneq/humann3_output_neon_rerun_v2/regrouped_scbi_sample_pathways_ko.tsv \
        --mapping  /home/juneq/humann3_output/unpacked_results/ko_to_xenobiotic_maps.tsv \
        --output   /home/juneq/humann3_output_neon_rerun_v2/scbi_xenobiotic_ko_abundance.tsv

Arguments:
    --abundance   Path to raw KO abundance TSV (no header, may have a commented header)
    --mapping     Path to KO→xenobiotic mapping TSV (must contain “KO” and “Map” columns)
    --output      Path for the filtered & merged output TSV
"""

import argparse
import re
from pathlib import Path
import pandas as pd

def main(args):
    abundance_path = Path(args.abundance)
    mapping_path   = Path(args.mapping)
    output_path    = Path(args.output)

    # Infer sample name from the abundance filename
    sample_name = abundance_path.stem

    # Part 1: Clean the raw KO abundance file
    # Part 1: Clean the raw KO abundance file
    ko_rows = []
    with abundance_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            gene_family, raw_val = parts[0], parts[1]

            # Match only KO identifiers followed by a pipe (e.g., K00001|) and exclude 'unclassified'
            m = re.match(r'^(K\d{5})\|(.*)', gene_family)
            if not m:
                continue
            if "unclassified" in gene_family.lower():
                continue
            ko = m.group(1)

            try:
                abundance = float(raw_val)
            except ValueError:
                continue
            ko_rows.append((ko, abundance))


    if not ko_rows:
        raise ValueError("No valid KO entries found in abundance file.")

    ko_abundance = pd.DataFrame(ko_rows, columns=["KO", sample_name])

    # Part 2: Load mapping and filter / merge
    ko_map = pd.read_csv(mapping_path, sep="\t", comment="#")
    if not {"KO", "Map"}.issubset(ko_map.columns):
        raise ValueError("Mapping file must contain 'KO' and 'Map' columns.")

    # Filter to only those KOs that have a map entry
    filtered = ko_abundance[ko_abundance["KO"].isin(ko_map["KO"])]
    if filtered.empty:
        print("Warning: No overlapping KOs found between abundance and mapping files.")

    # Merge on KO
    merged = filtered.merge(
        ko_map[["KO", "Map"]],
        on="KO",
        how="left"
    )

    # Reorder columns: KO, Map, abundance
    merged = merged[["KO", "Map", sample_name]]

    # Write output
    merged.to_csv(output_path, sep="\t", index=False)
    print(f"✅ Filtered & mapped KO abundance saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter raw KO abundance and map to xenobiotics")
    parser.add_argument(
        "--abundance", required=True,
        help="Raw KO abundance TSV (first col=gene family, second=abundance)"
    )
    parser.add_argument(
        "--mapping", required=True,
        help="KO→xenobiotic mapping TSV (columns: 'KO', 'Map')"
    )
    parser.add_argument(
        "--output", required=True,
        help="Output path for filtered & mapped TSV"
    )
    args = parser.parse_args()
    main(args)
