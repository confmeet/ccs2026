"""Build a per-attendee processing table from the raw registration export."""

import re

import numpy as np
import pandas as pd

SOURCE_CSV = "preprocessed_registration.csv"
OUTPUT_CSV = "breakout_table.csv"

BO_TITLES = {
    "Future directions for cyberinfrastructure": "BO1",
    "Sustainability of research software and CI": "BO2",
    "Building and retaining the CI workforce": "BO3",
    "Current challenges / concerns with AI / quantum Computing": "BO4",
    "Strategies for increasing the visibility of CyberTraining, SCIPE, and "
    "CSSI awards and their outputs (software, services, models, training "
    "materials, etc)": "BO5",
    "Pursuing, measuring, and communicating scientific and broader impacts": "BO6",
}

BO_COLUMNS = ["BO1", "BO2", "BO3", "BO4", "BO5", "BO6"]

RANK_TO_SCORE = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0}

EXCLUDED_REGTYPES = {"progman", "progman (comp)", "speaker"}

SESSION_LINE_RE = re.compile(r"^\s*(\d+)\s*-\s*(.+?)\s*$")
NAME_TOKEN_RE = re.compile(r"([ .])")
WHITESPACE_RE = re.compile(r"\s+")


def format_name(name):
    tokens = NAME_TOKEN_RE.split(name)
    formatted = []
    for token in tokens:
        if token in (" ", "."):
            formatted.append(token)
            continue
        lowered = token.lower()
        capitalized = re.sub(
            r"[a-z]", lambda m: m.group(0).upper(), lowered, count=1
        )
        formatted.append(capitalized)
    return "".join(formatted)


def parse_sessions(sessions_str):
    scores = {bo: 0 for bo in BO_TITLES.values()}
    if pd.isna(sessions_str):
        return scores
    for line in sessions_str.split("\n"):
        if not line.strip():
            continue
        match = SESSION_LINE_RE.match(line)
        if not match:
            continue
        rank, title = match.groups()
        bo = BO_TITLES.get(title.strip())
        if bo is None:
            continue
        scores[bo] = RANK_TO_SCORE.get(int(rank), 0)
    return scores


def parse_volunteering(volunteering_str):
    text = "" if pd.isna(volunteering_str) else volunteering_str
    return {
        "Fac": 1 if "Facilitator" in text else 0,
        "Scribe": 1 if "Scribe" in text else 0,
    }


def is_excluded_regtype(regtype):
    if pd.isna(regtype):
        return False
    normalized = WHITESPACE_RE.sub(" ", regtype.strip()).lower()
    return normalized in EXCLUDED_REGTYPES


def compute_capacities(n, sessions=BO_COLUMNS):
    base, extra = divmod(n, len(sessions))
    return {bo: base + (1 if i < extra else 0) for i, bo in enumerate(sessions)}


def assign_breakouts(df):
    """Greedily assign each row to a BO column, filling equal-sized groups
    while favoring each person's highest-scored session first."""
    capacities = compute_capacities(len(df))
    shuffled_index = np.random.permutation(df.index)

    pairs = [
        (df.loc[idx, bo], idx, bo) for idx in shuffled_index for bo in BO_COLUMNS
    ]
    pairs.sort(key=lambda pair: pair[0], reverse=True)

    assignment = {}
    remaining = dict(capacities)
    for _, idx, bo in pairs:
        if idx in assignment or remaining[bo] <= 0:
            continue
        assignment[idx] = bo
        remaining[bo] -= 1

    return df.index.map(assignment)


def build_table(source_csv=SOURCE_CSV):
    df = pd.read_csv(source_csv, skiprows=1)

    rows = []
    for _, row in df.iterrows():
        record = {"Name": format_name(row["Name"])}
        record.update(parse_sessions(row["Sessions"]))
        record.update(parse_volunteering(row["Volunteering"]))
        record["Excluded"] = is_excluded_regtype(row["RegType"])
        rows.append(record)

    columns = [
        "Name",
        "BO1",
        "BO2",
        "BO3",
        "BO4",
        "BO5",
        "BO6",
        "Fac",
        "Scribe",
        "Excluded",
    ]
    table = pd.DataFrame(rows, columns=columns)

    table["Breakout"] = ""
    eligible = table[~table["Excluded"]]
    table.loc[eligible.index, "Breakout"] = assign_breakouts(eligible)

    return table.drop(columns="Excluded")


if __name__ == "__main__":
    table = build_table()
    table.to_csv(OUTPUT_CSV, index=False)
    print(table.head())
    print(f"\nWrote {len(table)} rows to {OUTPUT_CSV}")
    print(table["Breakout"].value_counts())
