#!/usr/bin/env python3
"""
merge_metaphlan_bugs.py

Description:
    This script merges MetaPhlAn bugs list TSV files in a directory.
    It merges on the 'clade_name' column (first column) and pulls the third column
    (typically relative abundance) regardless of its header name.
    All abundance columns are renamed using the first word of each file name
    with "_abundance" as a suffix. Missing values are filled with 0.

Usage:
    python3 merge_metaphlan_bugs.py \
        --input_dir /path/to/bugs_lists/ \
        --output /path/to/merged_bugs.tsv
"""

import pandas as pd
from pathlib import Path
import argparse

def load_and_format(filepath):
    df = pd.read_csv(filepath, sep='\t', comment='#')
    df = df.iloc[:, [0, 2]]  # Extract first and third columns
    df.columns = ["clade_name", "abundance"]
    sample_name = filepath.stem.split('_')[0]
    df = df.rename(columns={"abundance": f"{sample_name}_abundance"})
    return df

def main():
    parser = argparse.ArgumentParser(description="Merge MetaPhlAn bugs list TSV files on clade_name.")
    parser.add_argument("--input_dir", required=True, help="Directory containing MetaPhlAn bugs list .tsv files.")
    parser.add_argument("--output", required=True, help="Path to output merged TSV file.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_file = Path(args.output)

    files = sorted(input_dir.glob("*.tsv"))
    if not files:
        raise FileNotFoundError(f"No .tsv files found in: {input_dir}")

    print(f"Merging {len(files)} MetaPhlAn bugs list files...")

    merged_df = load_and_format(files[0])
    for file in files[1:]:
        df = load_and_format(file)
        merged_df = pd.merge(merged_df, df, on="clade_name", how="outer")

    merged_df = merged_df.fillna(0)
    merged_df = merged_df.rename(columns={"clade_name": "Key"})  # Rename final first column to 'Key'
    merged_df.to_csv(output_file, sep="\t", index=False)
    print(f"Merged bugs list written to: {output_file}")

if __name__ == "__main__":
    main()
