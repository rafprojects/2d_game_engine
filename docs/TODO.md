# Project TODO / Tracking

A running list of important follow-ups to tackle "at some point." Not sprint
work — just things that shouldn't get lost. Started 2026-06-06 during M0 setup.

## Pre-publish / repo hygiene
- [ ] **Fix placeholder metadata in `pyproject.toml`** — the `Homepage`,
  `Documentation`, `Repository`, and `Bug Tracker` URLs still say
  `yourusername`, and the author is `Your Name <your.email@example.com>`.
  Update before any public release or PyPI publish.

## Licensing (decided, not yet applied)
- [ ] **Switch the core license MIT → Apache-2.0** — update the `license`
  field + classifier in `pyproject.toml` and add a top-level `LICENSE` file.
  (Apache-2.0 was chosen for the patent grant / commercial protection.)
- [ ] **Add a CLA** (Contributor License Agreement) + a CLA check/bot, to
  preserve relicensing / dual-license optionality before accepting outside
  contributions. Cheapest to set up now while there are zero contributors.

## CI / testing
- [ ] **Add the integration suite to CI** — currently only `tests/unit` runs
  (headless-safe). `tests/integration` needs a render context; wire up xvfb
  (Linux) or Panda3D offscreen mode before enabling it in the workflow.

## Misc
- [ ] **Decide on `PROJECT.md` placement** — it was committed as part of the
  M0 commit (`ebf1f78`) rather than on its own. Move or re-commit separately
  if you'd prefer it isolated.
