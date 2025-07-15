#!/usr/bin/env python3

import pandas as pd
import argparse
import os
import sys

def collapse_merged_bugs(input_file, output_file, taxonomic_level='genus'):
    """
    Collapse a merged MetaPhlAn bugs list to a specific taxonomic level,
    extracting only the name of the taxon at that level and ignoring entries with GGB.
    
    Parameters:
    -----------
    input_file : str
        Path to the merged MetaPhlAn bugs list file
    output_file : str
        Path to save the collapsed table
    taxonomic_level : str
        Taxonomic level to collapse to ('kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'all')
    """
    # Define taxonomy level prefixes
    level_prefixes = {
        'kingdom': 'k__',
        'phylum': 'p__',
        'class': 'c__',
        'order': 'o__',
        'family': 'f__',
        'genus': 'g__',
        'species': 's__'
    }

    # Validate the requested taxonomic level
    if taxonomic_level not in level_prefixes and taxonomic_level != 'all':
        print(f"Error: Invalid taxonomic level '{taxonomic_level}'")
        print(f"Valid options are: {', '.join(level_prefixes.keys())} or 'all'")
        return

    print(f"Reading merged bugs list from: {input_file}")

    # Manual parsing to handle header lines
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    # Skip the first row, use the second row as header
    header = lines[1].split('\t')
    data = []
    for line in lines[2:]:
        parts = line.split('\t')
        if len(parts) != len(header):
            print(f"Warning: Line has {len(parts)} fields, expected {len(header)}. Skipping.")
            continue
        data.append(parts)

    # Create DataFrame
    df = pd.DataFrame(data, columns=header)
    print(f"Parsed file with {df.shape[0]} rows and {df.shape[1]} columns.")

    # Identify the taxonomy column (first column)
    clade_column = df.columns[0]
    print(f"Using '{clade_column}' as taxonomy column")

    # Remove rows with 'GGB' from taxonomy
    ggb_count = df[df[clade_column].str.contains('GGB', na=False)].shape[0]
    if ggb_count > 0:
        print(f"Filtering out {ggb_count} entries containing 'GGB'")
        df = df[~df[clade_column].str.contains('GGB', na=False)]

    # Set taxonomy column as index
    df.set_index(clade_column, inplace=True)

    # Convert abundance columns to float safely
    for col in df.columns:
        if isinstance(col, str):
            try:
                series = df[col]
                if isinstance(series, pd.Series):
                    df[col] = pd.to_numeric(series, errors='coerce')
            except Exception as e:
                print(f"Warning: Could not convert column '{col}' to numeric. Error: {e}")


    df.fillna(0, inplace=True)

    if taxonomic_level == 'all':
        df.reset_index(inplace=True)
        df = df.rename(columns={df.columns[0]: 'Key'})
        df.to_csv(output_file, sep='\t', index=False, float_format='%.8f')
        print(f"Full table saved to: {output_file}")
        return

    target_prefix = level_prefixes[taxonomic_level]
    collapsed_data = {}

    for clade, row in df.iterrows():
        if not isinstance(clade, str) or 'GGB' in clade:
            continue

        if '|' in clade:
            parts = clade.split('|')
            target = [p for p in parts if p.startswith(target_prefix)]
            if not target:
                continue
            taxon_name = target[0].replace(target_prefix, '')
        else:
            if not clade.startswith(target_prefix):
                continue
            taxon_name = clade.replace(target_prefix, '')

        # Ensure numeric row before summing
        numeric_row = row.astype(float)

        if taxon_name not in collapsed_data:
            collapsed_data[taxon_name] = numeric_row.copy()
        else:
            collapsed_data[taxon_name] += numeric_row

    # Output collapsed table
    if collapsed_data:
        collapsed_df = pd.DataFrame(collapsed_data).T
        collapsed_df.reset_index(inplace=True)
        collapsed_df = collapsed_df.rename(columns={'index': 'Key'})

        with open(output_file, 'w') as f:
            f.write(lines[0] + '\n')
            collapsed_df.to_csv(f, sep='\t', index=False, float_format='%.8f')

        print(f"Collapsed table saved to: {output_file}")
        print(f"Reduced from {len(df)} to {len(collapsed_df)} taxa at {taxonomic_level} level")
    else:
        print("No taxa matched the specified level.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Collapse merged MetaPhlAn bugs list to specific taxonomic level.')
    parser.add_argument('--input_file', required=True, help='Path to the merged MetaPhlAn bugs list file')
    parser.add_argument('--output_file', required=True, help='Path to save the collapsed table')
    parser.add_argument('--level', default='genus',
                        choices=['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'all'],
                        help='Taxonomic level to collapse to')

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)

    collapse_merged_bugs(args.input_file, args.output_file, args.level)
