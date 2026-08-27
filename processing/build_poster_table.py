"""Assign posters (one per presented award) to sessions and board positions."""

import numpy as np
import pandas as pd

from processing.build_breakout_table import format_name

SOURCE_CSV = "preprocessed_registration.csv"
OUTPUT_CSV = "poster_table.csv"

SESSION_LABELS = ["Session I", "Session II", "Session III", "Session IV"]


def collect_posters(source_csv=SOURCE_CSV):
    df = pd.read_csv(source_csv, skiprows=1)

    posters = []
    for _, row in df.iterrows():
        for award_num in (1, 2, 3):
            award = row[f"Award #{award_num}"]
            if pd.isna(award):
                continue
            if "Presenting: Yes" not in award:
                continue
            posters.append(
                {
                    "Name": format_name(row["Name"]),
                    "AwardNum": award_num,
                    "PosterRand": np.random.uniform(0, 1),
                }
            )
    return pd.DataFrame(posters, columns=["Name", "AwardNum", "PosterRand"])


def assign_sessions(posters):
    posters = posters.sort_values("PosterRand", ignore_index=True)
    split_points = np.array_split(np.arange(len(posters)), len(SESSION_LABELS))

    assigned = []
    for label, indices in zip(SESSION_LABELS, split_points):
        group = posters.iloc[indices].copy()
        group["PosterSession"] = label
        group["PosterPosition"] = range(1, len(group) + 1)
        assigned.append(group)

    return pd.concat(assigned, ignore_index=True)


def build_table(source_csv=SOURCE_CSV):
    posters = collect_posters(source_csv)
    assigned = assign_sessions(posters)
    columns = ["Name", "AwardNum", "PosterRand", "PosterSession", "PosterPosition"]
    return assigned.sort_values("Name", ignore_index=True)[columns]


if __name__ == "__main__":
    table = build_table()
    table.to_csv(OUTPUT_CSV, index=False)
    print(table.head())
    print(f"\nWrote {len(table)} posters to {OUTPUT_CSV}")
    print(table["PosterSession"].value_counts())
