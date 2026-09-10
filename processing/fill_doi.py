"""Fill in missing DOI values in the site's assignments CSV from the Figshare
DOI submission form responses.

Matches form respondents (First Name(s) + Last Name(s)) to rows in
assets/data/assignments.csv by name, and fills in any blank "doi" cells.
Existing doi values are never overwritten. A respondent who submitted
multiple posters (multiple form rows) gets all of their DOIs joined with
"; ", in submission order, matching how the "poster" column already lists
multiple board assignments.

Note: layouts/_default/assignments.html renders the doi cell as a single
<a href="{{ .doi }}">, so a person with more than one DOI will display a
semicolon-joined string that is not a single valid link target. That's a
template limitation, not something this script can fix.
"""

import re
from collections import defaultdict

import pandas as pd

FORM_CSV = "2026 CSSI-Cybertraining-SCIPE Figshare DOIs (Responses) - Form Responses 1.csv"
ASSIGNMENTS_CSV = "../assets/data/assignments.csv"

DOI_RE = re.compile(r"10\.\d{4,9}/\S+")


def normalize_name(name):
    return re.sub(r"\s+", " ", name.strip())


def match_key(name):
    """Key used to match a form respondent to an assignments.csv row.

    Case-insensitive: form respondents don't reliably capitalize their own
    name the same way twice (e.g. a repeat submitter entering "peter
    lauritzen" the second time round), and matches must still land on the
    single canonical assignments.csv row.
    """
    return normalize_name(name).casefold()


def normalize_doi(raw):
    raw = raw.strip()
    match = DOI_RE.search(raw)
    if not match:
        return None
    return f"https://doi.org/{match.group(0)}"


def fill_doi(assignments_csv=ASSIGNMENTS_CSV, form_csv=FORM_CSV):
    form = pd.read_csv(form_csv)
    form["Name"] = (
        form["First Name(s)"].str.strip() + " " + form["Last Name(s)"].str.strip()
    ).map(normalize_name)
    form["DOI"] = form["Figshare DOI"].map(normalize_doi)

    table = pd.read_csv(assignments_csv, keep_default_na=False)
    idx_by_key = {match_key(name): idx for idx, name in table["name"].items()}

    # pandas coerces a Python None returned from .map() into float NaN, so
    # check with pd.isna/pd.notna rather than plain truthiness (NaN is truthy).
    dois_by_idx = defaultdict(list)
    malformed, unmatched = [], []
    for name, raw, doi in zip(form["Name"], form["Figshare DOI"], form["DOI"]):
        if pd.isna(doi):
            malformed.append((name, raw))
            continue
        idx = idx_by_key.get(match_key(name))
        if idx is None:
            unmatched.append((name, doi))
            continue
        dois_by_idx[idx].append(doi)

    filled, skipped_existing = [], []
    for idx, dois in dois_by_idx.items():
        name = table.at[idx, "name"]
        if table.at[idx, "doi"]:
            skipped_existing.append(name)
            continue
        # Repeat/duplicate form submissions of the same poster (e.g. a
        # respondent resubmitting with the DOI in a different format)
        # shouldn't produce a repeated link — dedupe, preserving order.
        deduped = list(dict.fromkeys(dois))
        table.at[idx, "doi"] = "; ".join(deduped)
        filled.append(name)

    return table, filled, skipped_existing, unmatched, malformed


if __name__ == "__main__":
    table, filled, skipped_existing, unmatched, malformed = fill_doi()
    table.to_csv(ASSIGNMENTS_CSV, index=False)

    print(f"Filled {len(filled)} DOI value(s):")
    for name in filled:
        print(f"  {name}")

    if skipped_existing:
        print(f"\nSkipped {len(skipped_existing)} name(s) that already had a DOI:")
        for name in skipped_existing:
            print(f"  {name}")

    if malformed:
        print(f"\nWARNING: {len(malformed)} form response(s) had a Figshare DOI that could not be parsed (expected something containing 10.xxxx/...):")
        for name, raw in malformed:
            print(f"  {name}: {raw!r}")

    if unmatched:
        print(f"\nWARNING: {len(unmatched)} name(s) from the form had no match in assignments.csv:")
        for name, doi in unmatched:
            print(f"  {name}: {doi}")

    print(f"\nWrote {ASSIGNMENTS_CSV}")
