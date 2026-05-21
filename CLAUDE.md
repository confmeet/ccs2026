# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Hugo-based single-page conference website for the 2026 NSF CSSI / CyberTraining / SCIPE PI Meeting.
Deployed to: `https://confmeet.github.io/ccs2026/`

## Commands

```bash
# Start local dev server (localhost:1313, live reload)
hugo server -D

# Build for production (output to ./public/)
hugo --gc --minify

# After cloning, initialize the theme submodule
git submodule update --init --recursive
```

## Architecture

**Theme:** `jweslley/hugo-conference` (git submodule at `themes/hugo-conference/`). Single-page design — all content lives on one scrollable page with anchor-linked navigation.

**All content and configuration lives in `config.yml`** — no Markdown content files. The theme reads everything from `params`:
- `Schedule` array drives both the **Speakers** section (items with a `presentation` key) and the **Program** table
- `Registration`, `PosterSession`, `Childcare` are custom param blocks consumed by custom partials

**Custom partials** (in `layouts/partials/`) extend the theme with sections it doesn't have built-in:
- `registration.html` — reads `.registration`
- `posters.html` — reads `.postersession`
- `childcare.html` — reads `.childcare`

**Section order** is controlled by the `Sections` array in `config.yml`. To add, remove, or reorder sections, edit that array (and add a matching entry to `Titles`).

**Custom CSS** is in `static/css/custom.css` and is injected via the overridden `layouts/index.html` (the theme has no custom head hook). Currently provides dark mode table styling for the schedule.

## Adding a Speaker

In `config.yml`, add an entry to the appropriate day's `schedule` array with a `presentation` key. Entries without a `presentation` key appear only in the Program table as session/break rows.

```yaml
Days:
  - name: "Day 1 — Monday, June 15"
    schedule:
      - name: "Jane Smith"
        photo: "/img/speakers/jane-smith.jpg"  # place file in static/img/speakers/
        bio: "Jane is a professor at..."
        company: "University of X"
        link:
          href: "https://janesmith.example.com"
          text: "janesmith.example.com"
        presentation:
          title: "Talk Title Here"
          description: "Abstract text..."
          time: "10:00am"
      - name: "Lunch"
        time: "12:00pm"
```

The `Speakers` section automatically collects all entries with a `presentation` key across all days. To add a third day, add another `- name: / schedule:` block to `Days`.

## Deployment

GitHub Actions (`.github/workflows/hugo.yaml`) builds with Hugo 0.147.0 extended and deploys to GitHub Pages on every push to `main`. The `submodules: recursive` checkout step is required for the theme.

To enable GitHub Pages on a new repo: **Settings → Pages → Source → GitHub Actions**.
