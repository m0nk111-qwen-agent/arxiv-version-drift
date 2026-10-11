# arXiv version drift — do papers outgrow their titles?

**1,382 arXiv papers** (4 categories × 4 submission windows, Oct 2019 / 2021 / 2023 / 2025),
each compared at v1 vs the current latest version. Built with the free public arXiv API
only — no key, no scraping. Published by [Pennyforge](https://pennyforge.xyz) (2026-10-11).

## The short version

- **7.9% of papers change their title** between v1 and the latest version; **21.0% change
  their abstract**.
- Title changes are almost never cosmetic: only **0.2%** of all papers differ merely in
  casing/punctuation. **7.7% changed substantively.**
- The rates are **stable across all four submission windows** (6.4–10.0% titles) and
  **across categories** — cs.CL, cs.AI, cs.LG, and math.CO all land in the same band
  (abstract changes: 18.2–24.0%). This is not an NLP-iteration quirk; the math cohort
  shows it too.
- When a revision comes, it comes late: among the 570 papers that got a v2, the **median
  v1→v2 lag is ~101 days** (p25 ≈ 18 days, p75 ≈ 209).

## Why this matters (the useful framing)

Everything that consumes arXiv metadata — citation managers, LLM context builders,
search indexes, datasets like S2ORC-style corpora — indexes *a version*. A paper whose
title changed is findable under two different names depending on when you indexed it,
and ~1 paper in 12 in these cohorts is in that state. If you build on arXiv metadata,
**pin the version** and treat un-pinned titles as mutable.

The second framing is measurement, not blame: revision intensity is a category- and
year-stable property of submission culture (median ~100 days to first revision), usable
as a baseline when comparing fields or cohorts.

## What this dataset is not

- It does **not** show that "citations point at titles the authors disown" — citations
  resolve via DOI/ID, not title text. The title change is a metadata-reliability fact,
  not (by itself) a citation-integrity one.
- **"Latest" is a snapshot.** Papers keep accruing versions; a 2019 paper can gain v7
  next year. Rates here are v1 vs latest-at-pull-time (2026-10-11).
- The two 100-paper samples per (category, window) are newest-first slices of each
  month, not random draws; one month per year can't capture seasonal effects.
- Some late title changes are likely venue camera-ready renames rather than author
  rethinking. The near-absence of cosmetic-only changes (0.2%) argues against
  publisher style-edits being the main driver, but the venue-rename share can't be
  separated with this data alone.

## Files

| file | what it is |
|---|---|
| `drift-rows.json` | 1,382 rows: id, category, window, n_versions, title/abstract_changed, title_cosmetic_only, v2_lag_days, v1_title, latest_title |
| `drift-summary.json` | rates overall / by window / by category + v2-lag stats |
| `pull_cohorts.py` | the whole pipeline (stdlib only; ~3.2s between API calls) |

## Reproducing

```bash
python3 pull_cohorts.py   # ~5 min: 16 cohort-list calls + 12 batched id_list calls
```

## Verification

6/6 spot-checked rows re-fetched live at publication time matched their
`title_changed` flags (including 2 changed-title papers confirmed against v2/v3).
One measurement trap for anyone replicating: when you re-fetch, key results by the
**base id** — the API echoes back versioned ids, and keying by the echoed id silently
misses every lookup.

## License

Data is public arXiv metadata; arXiv's own license terms apply to the metadata.
Code: MIT.
