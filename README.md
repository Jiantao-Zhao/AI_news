# AI4Science Literature Sweep

Personal research-tracking workspace for AI for Science literature. Maintains structured, bilingual literature surveys with primary-source PDFs across four priority areas:

- **AI for molecules** — generative models, diffusion/flow matching, property prediction, retrosynthesis, drug discovery
- **AI for enzymes/proteins** — protein language models (ESM-3, ProGen, ZymCTRL), structure prediction (AlphaFold, Boltz), enzyme design, ML-guided evolution
- **AI for soft materials** — polymers, self-assembly, coarse-grained MD + ML, inverse design, rheology
- **AI4Science cross-cutting** — scientific foundation models (Evo 2), retrieval-augmented LLMs, autonomous labs

## Skills

Three self-contained skills automate the literature survey workflow, one per agent platform:

| Platform | Location | Capabilities |
|---|---|---|
| **Claude Code** | `.claude/skills/ai4science-literature-sweep/` | Full Playwright automation for JS-rendered journals & Cloudflare-protected PDFs |
| **Opencode** | `.opencode/skills/ai4science-literature-sweep/` | curl/webfetch based (no browser); requires `OPENCODE_ENABLE_EXA=1` for websearch |
| **OpenClaw** | `.agents/skills/ai4science-literature-sweep/` | Full Playwright + sub-agent orchestration via `task` tool |

Each run produces a dated folder with bilingual reports, downloaded PDFs, and **markdown bundles auto-derived from each PDF** (figure index + extracted images + body text).

## Per-run output layout

```
YYYY-MM-DD/
├── report.md          # English narrative — required
├── report_zh.md       # Chinese narrative — required, structurally parallel
├── papers/            # Downloaded PDFs, <FirstAuthor><Year>_<slug>.pdf
├── markdown/          # Auto-derived bundles, 1:1 with papers/
│   ├── _index.json    # Per-PDF stats {n_figures, embedded, page_render, md_chars}
│   └── <basename>/<basename>.md  + figures/   # Figure index + body text + extracted PNGs
└── raw/               # Landing-page metadata JSON, full-text dumps, search results
```

Dated folders are intentionally git-ignored (each holds tens of MB of PDFs); only the skill machinery lives in version control.

## Version history

### 2026-04-28 — PDF→markdown pipeline embedded into the skill

- New helper `pdf-to-markdown.py` (PyMuPDF + markitdown) auto-converts every downloaded PDF into a markdown bundle: figure-index table at the top, embedded images exported per-page, full-page rasters at 150 DPI as a fallback for chart-heavy vector pages (≥50 vector paths and zero embedded images). Idempotent — re-running on the same `papers/` skips bundles that already exist unless `--force`.
- Skill workflow grew from 8 to 9 steps: a new Step 7 runs the helper after every download batch, and Step 8 reads the markdown bundle (faster + figure index up front) instead of the raw PDF.
- Output contract gained the required `markdown/` subfolder. Every PDF in `papers/` must have a matching bundle in `markdown/<basename>/`.
- All three port copies (Claude Code / Opencode / OpenClaw) updated and now share the bundled venv at `~/.claude/skills/ai4science-literature-sweep/.venv/` (PyMuPDF + markitdown). Each port's SKILL.md documents how to set up a local fallback venv if the shared one is unavailable.
- `.gitignore` strengthened to exclude `.venv/`, `__pycache__/`, and `.playwright-mcp/` runtime caches.

### 2026-04-24 — Initial three-port skill release

- Bilingual report scaffold (English + Chinese, structurally parallel).
- Path A/B/C/D/E download decision table covering arXiv, OA journals, JS-rendered publishers, Cloudflare-protected bioRxiv, and closed-access fallback.
- Playwright in-session `fetch()` (Path C) for bioRxiv — bypasses curl 403 by inheriting the browser's `cf_clearance` cookie.
- `playwright-extract.js` for landing-page metadata, `playwright-fetch-pdf.js` for the bioRxiv PDF byte-stream.
- Grounding discipline: every numerical claim must be backed by primary PDF or full-text JSON; search-snippet claims are tagged `[search-only, unverified]`.
- Filename discipline: first-author surname must come from the landing page's `citation_author[0]`, never from URL or DOI.
