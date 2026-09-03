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

import pandas as pd

FORM_CSV = "2026 CSSI-Cybertraining-SCIPE Figshare DOIs (Responses) - Form Responses 1.csv"
ASSIGNMENTS_CSV = "../assets/data/assignments.csv"

DOI_RE = re.compile(r"10\.\d{4,9}/\S+")


def normalize_name(name):
    return re.sub(r"\s+", " ", name.strip())


def normalize_doi(raw):
    raw = raw.strip()
    match = DOI_RE.search(raw)
    if not match:
        return None
    return f"https://doi.org/{match.group(0)}"


def build_doi_by_name(form_csv=FORM_CSV):
    form = pd.read_csv(form_csv)
    form["Name"] = (
        form["First Name(s)"].str.strip() + " " + form["Last Name(s)"].str.strip()
    ).map(normalize_name)
    form["DOI"] = form["Figshare DOI"].map(normalize_doi)

    doi_by_name = {}
    for name, group in form.groupby("Name", sort=False):
        dois = [d for d in group["DOI"] if d]
        if dois:
            doi_by_name[name] = "; ".join(dois)
    return doi_by_name


def fill_doi(assignments_csv=ASSIGNMENTS_CSV, form_csv=FORM_CSV):
    doi_by_name = build_doi_by_name(form_csv)
    table = pd.read_csv(assignments_csv, keep_default_na=False)

    filled, skipped_existing, unmatched = [], [], []
    for name, doi in doi_by_name.items():
        matches = table.index[table["name"].map(normalize_name) == name]
        if len(matches) == 0:
            unmatched.append(name)
            continue
        idx = matches[0]
        if table.at[idx, "doi"]:
            skipped_existing.append(name)
            continue
        table.at[idx, "doi"] = doi
        filled.append(name)

    return table, filled, skipped_existing, unmatched


if __name__ == "__main__":
    table, filled, skipped_existing, unmatched = fill_doi()
    table.to_csv(ASSIGNMENTS_CSV, index=False)

    print(f"Filled {len(filled)} DOI value(s):")
    for name in filled:
        print(f"  {name}")

    if skipped_existing:
        print(f"\nSkipped {len(skipped_existing)} name(s) that already had a DOI:")
        for name in skipped_existing:
            print(f"  {name}")

    if unmatched:
        print(f"\nWARNING: {len(unmatched)} name(s) from the form had no match in assignments.csv:")
        for name in unmatched:
            print(f"  {name}")

    print(f"\nWrote {ASSIGNMENTS_CSV}")
