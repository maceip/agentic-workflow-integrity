# Publishing pipeline

All public output — code, research results, and story — publishes from this
repository. Three content layers exist, with a strict derivation order.

## Layer 1: canonical sources (write correctly first)

| Content | Canonical source |
|---|---|
| Research design | `DESIGN.md` |
| Code | `awi/`, `experiments/` |
| Research results | `results/` (machine-written by experiment runs) |
| Story | `story/pages.json` (one page = one atomic content unit) |

## Layer 2: website rendering

`story/build_story.py` validates `story/pages.json` and renders
`story/storybook.html` plus `story/PAGES.md`. Research results render from
`results/*.json` and `results/report.md`. Website pages link story pages to
research references; story text never carries a measurement.

## Layer 3: social distillation (secondary, later)

Each atomic unit may later be distilled into a Twitter post with the page
image attached. Rules:

- Distillation happens only after the canonical text for the unit is
  approved as correct. Correct first, small second.
- A distillation may shorten. A distillation may never strengthen a claim
  beyond the research references on the source page.
- `story/pages.json` holds one `distillation.twitter` slot per page.
  `not_yet_distilled` with `text: null` is the deliberate initial state.
- `story/build_story.py` enforces the character limit and renders the
  status ledger at `story/distillations/TWITTER_DRAFTS.md`.
- No tool in this repository posts to Twitter. Posting is a human action
  outside the repository.
