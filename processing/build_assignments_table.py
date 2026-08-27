"""Merge the breakout and poster tables into the site's assignments CSV."""

import pandas as pd

from processing.build_breakout_table import BO_TITLES

BREAKOUT_CSV = "breakout_table.csv"
POSTER_CSV = "poster_table.csv"
OUTPUT_CSV = "../assets/data/assignments.csv"

BO_CODE_TO_TITLE = {code: title for title, code in BO_TITLES.items()}

# Shortened for display — the full BO_TITLES wording is too long for the table column.
BO_CODE_TO_TITLE["BO5"] = "Strategies for increasing the visibility of awards and outputs"

BO_ROOMS = {
    "BO1": "Strathmore A",
    "BO2": "Strathmore B",
    "BO3": "Glen Echo",
    "BO4": "Forest Glen",
    "BO5": "White Oak A",
    "BO6": "White Oak B",
}


def format_breakout(code):
    if pd.isna(code) or code == "":
        return ""
    return f"{BO_CODE_TO_TITLE[code]} — {BO_ROOMS[code]}"


def format_poster(rows):
    entries = [
        f"{row.PosterSession}, Board {row.PosterPosition}" for row in rows.itertuples()
    ]
    return "; ".join(entries)


def build_table(breakout_csv=BREAKOUT_CSV, poster_csv=POSTER_CSV):
    breakout = pd.read_csv(breakout_csv).drop_duplicates("Name", keep="first")
    poster = pd.read_csv(poster_csv)

    names = sorted(set(breakout["Name"]) | set(poster["Name"]))

    breakout_by_name = breakout.set_index("Name")["Breakout"]
    poster_by_name = {name: group for name, group in poster.groupby("Name")}

    rows = []
    for name in names:
        breakout_code = breakout_by_name.get(name, "")
        poster_rows = poster_by_name.get(name)
        rows.append(
            {
                "name": name,
                "breakout": format_breakout(breakout_code),
                "poster": format_poster(poster_rows) if poster_rows is not None else "",
                "doi": "",
            }
        )

    return pd.DataFrame(rows, columns=["name", "breakout", "poster", "doi"])


if __name__ == "__main__":
    table = build_table()
    table.to_csv(OUTPUT_CSV, index=False)
    print(table.head())
    print(f"\nWrote {len(table)} rows to {OUTPUT_CSV}")
