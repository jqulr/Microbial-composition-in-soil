import pandas as pd
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser(description="Map KEGG map IDs to human-readable pathway names.")
    parser.add_argument("--input", required=True, help="Input TSV file with KO and KEGG Map columns.")
    parser.add_argument("--output", required=True, help="Output TSV file with mapped pathway names.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Load the KO abundance+map table
    df = pd.read_csv(input_path, sep="\t")
    df.columns = df.columns.str.strip()

    # Split the comma-separated map IDs into lists
    df["Map"] = df["Map"].fillna("").apply(lambda x: x.split(",") if x else [])
    df = df.explode("Map")
    df["Map"] = df["Map"].str.strip()

    # Mapping of KEGG map IDs to pathway names
    map_id_to_name = {
        "map00361": "Chlorocyclohexane and chlorobenzene degradation",
        "map00362": "Benzoate degradation",
        "map00364": "Fluorobenzoate degradation",
        "map00621": "Dioxin degradation",
        "map00622": "Xylene degradation",
        "map00623": "Toluene degradation",
        "map00624": "Polycyclic aromatic hydrocarbon degradation",
        "map00625": "Chloroalkane and chloroalkene degradation",
        "map00626": "Naphthalene degradation",
        "map00627": "Aminobenzoate degradation",
        "map00633": "Nitrotoluene degradation",
        "map00642": "Ethylbenzene degradation",
        "map00643": "Styrene degradation",
        "map00930": "Caprolactam degradation",
        "map00980": "Metabolism of xenobiotics by cytochrome P450",
        "map00982": "Drug metabolism - cytochrome P450",
        "map00983": "Drug metabolism - other enzymes",
        "map00984": "Steroid degradation",
        "map00363": "Bisphenol degradation",
        "map00365": "Furfural degradation",
        "map00791": "Atrazine degradation"
    }
    df["Pathway_Name"] = df["Map"].map(map_id_to_name).fillna(df["Map"])

    # Drop the KO column
    df = df.drop(columns=["KO"], errors='ignore')

    # Group by map and sum all numeric columns
    grouped_df = df.groupby("Map", as_index=False).sum(numeric_only=True)

    # Reattach pathway names
    map_to_name = (
        df[["Map", "Pathway_Name"]]
        .drop_duplicates()
        .groupby("Map")["Pathway_Name"]
        .first()
        .reset_index()
    )
    grouped_df = grouped_df.merge(map_to_name, on="Map", how="left")

    # Reorder columns: Pathway_Name first
    cols = ["Pathway_Name"] + [c for c in grouped_df.columns if c not in ("Pathway_Name", "Map")]
    grouped_df = grouped_df[cols]

    # Save output
    grouped_df.to_csv(output_path, sep="\t", index=False)
    print("File saved to:", output_path)

if __name__ == "__main__":
    main()

