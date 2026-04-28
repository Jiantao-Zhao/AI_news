---
name: ai4science-literature-sweep
description: Find, download, and summarize recent AI-for-science research (molecules, enzymes, soft materials, protein language models, polymers, foundation models, autonomous labs). Run periodic AI4Science literature updates into a dated folder with primary-source PDFs and a bilingual report. Use when the user asks to search or sweep AI4Science literature. Playwright, agent-reach, and webfetch are all available.
---

# AI4Science literature sweep (OpenClaw)

One invocation produces one dated folder in the current working directory containing: a bilingual narrative summary report (English + Chinese, structurally parallel), primary-source PDFs downloaded end-to-end for every paper cited, **markdown bundles automatically derived from each PDF (text + figure index + extracted images)**, structured bibliographic metadata, and a dedupe-aware record of what was covered.

## Output contract — non-negotiable

```
$PWD/YYYY-MM-DD/
├── report.md         English narrative — required
├── report_zh.md      Chinese narrative — required, structurally parallel to report.md
├── papers/           Downloaded PDFs, <FirstAuthor><Year>_<slug>.pdf, ASCII only
├── markdown/         Auto-derived markdown bundles, one per PDF — required
│   ├── _index.json   Per-PDF stats {pdf, md, n_figures, embedded, page_render, md_chars}
│   └── <basename>/<basename>.md  + figures/  (1:1 with papers/<basename>.pdf)
└── raw/              Landing-page metadata JSON, full-text extraction JSON, search dumps
```

`YYYY-MM-DD` = today's date. **Both report files are mandatory in every run. Every PDF in `papers/` must have a matching bundle in `markdown/<basename>/`.** Nothing goes in the root of `$PWD`.

## Available tools in OpenClaw

- **Web search**: Use the `agent-reach` skill for platform-aware search (web, Twitter, Reddit, arXiv, etc.) or the `autoglm-websearch` tool for general web search. Brave search is configured in openclaw.json.
- **Playwright** (`mcp__plugin_playwright_playwright__*`): Full browser automation for JS-rendered journal pages and Cloudflare-protected PDFs.
- **`webfetch`**: For quick abstract-page fetches (arXiv, DOI resolver).
- **`task`** (sub-agent spawning): For parallel discovery across priority areas.
- **`bash`**: For curl-based PDF downloads, the `pdf-to-markdown.py` helper, and file operations.
- **`read`**: For reading downloaded PDFs and (preferably) the markdown bundles.
- **`write` / `edit`**: For writing report files.

## Prerequisites

- Python 3 with PyMuPDF + markitdown for the PDF→markdown bundle helper. The Claude Code copy of this skill ships a venv at `~/.claude/skills/ai4science-literature-sweep/.venv/` that all three port copies (Claude / Opencode / OpenClaw) share. If that venv is missing, create one alongside this skill: `uv venv ~/.agents/skills/ai4science-literature-sweep/.venv && uv pip install --python ~/.agents/skills/ai4science-literature-sweep/.venv/bin/python pymupdf 'markitdown[pdf]'`.

## Workflow — 9 steps, in order

1. **Load scope.** Read the sibling `scope.md` for priority areas and venue rankings. If `$PWD/.ai4science-scope.md` exists, it overrides.

2. **Dedupe prior runs.** Compute the set of DOIs and arXiv IDs already covered:
   ```
   grep -hrE '10\.[0-9]{4,}/[^ )]+|arXiv:[0-9]{4}\.[0-9]+' $PWD/*/report.md 2>/dev/null \
     | grep -oE '(10\.[0-9]{4,}/[^ )]+|arXiv:[0-9]{4}\.[0-9]+)' | sort -u
   ```
   Any hit matching an ID in this set is skipped.

3. **Create today's folder.** `mkdir -p $PWD/YYYY-MM-DD/papers $PWD/YYYY-MM-DD/raw $PWD/YYYY-MM-DD/markdown`.

4. **Discover in parallel.** Use the `task` tool to spawn sub-agents for each priority area in a single invocation. Each sub-agent uses agent-reach or autoglm-websearch to search. Restrict to current + previous calendar year. Rank: peer-reviewed > preprint, primary > review. Sub-agents return their findings; you consolidate.

5. **Verify first-author surnames from landing pages before naming anything.** The authoritative source is the landing page's `citation_author[0]` meta tag. Two extraction routes:
   - **Nature / Science / ACS / RSC / Cell** landing pages: use Playwright navigate + `playwright-extract.js` in `browser_evaluate` with `filename: "raw/<slug>_metadata.json"`.
   - **arXiv abstract page**: `citation_author` meta tags are on `https://arxiv.org/abs/<id>`. Use `webfetch` or Playwright.
   - **bioRxiv**: Playwright navigate (deals with Cloudflare), then extract metadata.

6. **Download — lightest tool that works. Escalate only on failure.**

   | Source | Path | Why |
   |---|---|---|
   | arXiv | **A** `curl -L --fail --max-time 60 -o papers/<name>.pdf https://arxiv.org/pdf/<id>` | No bot protection |
   | PMC / ChemRxiv / OA journals | **A** with `-A "$UA"` (Mozilla string) | Most OA journals accept |
   | Nature Commun. / npj / Science Advances OA | **A** with UA — `https://www.nature.com/articles/<id>.pdf` | Works when page is OA |
   | Nature / Science / ACS / RSC / Cell landing page | **B** Playwright navigate → `playwright-extract.js` in `browser_evaluate` → curl returned `pdf_url` with UA | Need JS render for metadata |
   | **bioRxiv** | **C** Playwright navigate → wait ~6 s for Cloudflare → `playwright-fetch-pdf.js` in `browser_evaluate` (uses `credentials: 'include'` to inherit cf_clearance) → python base64-decode | curl returns HTTP 403 even with UA |
   | Any site where A / B / C all fail | **D** `browser_evaluate` to dump rendered article text to `raw/<slug>_fulltext.json` | Valid grounding |
   | Closed-access paper | **E** Metadata + abstract only, mark "closed access" in the report, move on | Never route around paywalls |

   **Canonical Path C for bioRxiv:**
   ```javascript
   // In browser_evaluate with filename: "raw/<slug>_pdf_b64.json"
   async () => {
     const r = await fetch('<citation_pdf_url>', { credentials: 'include' });
     if (r.status !== 200) return { error: `HTTP ${r.status}` };
     const buf = new Uint8Array(await r.arrayBuffer());
     if (!new TextDecoder().decode(buf.slice(0, 5)).startsWith('%PDF'))
       return { error: 'not a PDF' };
     let bin = ''; const CHUNK = 0x8000;
     for (let i = 0; i < buf.length; i += CHUNK)
       bin += String.fromCharCode.apply(null, buf.subarray(i, i + CHUNK));
     return { size: buf.length, pdf_b64: btoa(bin) };
   }
   ```
   ```bash
   python3 -c "import json,base64; d=json.load(open('raw/<slug>_pdf_b64.json')); \
     open('papers/<FirstAuthor><Year>_<slug>.pdf','wb').write(base64.b64decode(d['pdf_b64']))"
   file papers/<...>.pdf   # expect "PDF document, version X.Y, N pages"
   rm raw/<slug>_pdf_b64.json
   ```
   Always `browser_close` at the end of a Playwright session.

7. **Convert every downloaded PDF to a markdown bundle — no exceptions.** Run the bundled helper once per sweep, after all PDFs are in `papers/`:
   ```bash
   ~/.claude/skills/ai4science-literature-sweep/.venv/bin/python \
     ~/.claude/skills/ai4science-literature-sweep/pdf-to-markdown.py \
     --out YYYY-MM-DD/markdown YYYY-MM-DD/papers
   ```
   (If the Claude Code venv is unavailable, point to the local fallback set up in Prerequisites.)
   The helper is **idempotent** — re-running on the same papers folder skips already-converted bundles unless `--force` is passed. What it produces: `markdown/<basename>/<basename>.md` (figure index table at the top + body text via markitdown), `markdown/<basename>/figures/p<NN>_*.png` (embedded images and full-page rasters at 150 DPI for chart-heavy vector pages with ≥50 paths), `markdown/_index.json` with one record per PDF. **No PDF in `papers/` is allowed to lack a bundle.**

8. **Read every markdown bundle before writing the report — no exceptions.** Use `read` on `markdown/<basename>/<basename>.md` (faster + cleaner than the raw PDF — figure index is right at the top). Read pages 1–8 worth of content for short papers, more for reviews. Every PDF in `papers/` must contribute paper-specific content to `report.md` — actual methods, numerical results with units, limitations. Citation-row-only appearance is the defining grounding failure: the narrative was built from search snippets, not from what was downloaded. If time is short, download fewer PDFs — do not skip the read.

9. **Write both reports in parallel structure.** Use `report-template.md` and `report-template-zh.md` as scaffolds. Four sections (one per priority area). Translate idiomatically for Chinese version. End with "Reading-priority recommendation", "Local downloads" table, and "Caveats / known gaps".

## Grounding discipline — the load-bearing rule

Every bullet must be backed by one of these, in order:
1. **The paper's markdown bundle in `markdown/<basename>/`** — preferred (Step 7 ensures it exists).
2. **Landing page abstract or fulltext in `raw/`** — for papers where Step 6 returned no PDF. Cite the JSON file in the downloads table.
3. **Search snippet** — allowed for discovery pointers only; tag every such bullet `[search-only, unverified]`.

A numerical claim must come from category 1 or 2. **Never launder a search-snippet number without the tag.**

## Filename discipline

- PDFs: `<FirstAuthorLastName><Year>_<short-slug>.pdf`. ASCII only, no spaces. Append `_preprint` for arXiv / bioRxiv. Example: `Singh2025_autonomous-enzyme-platform.pdf`.
- Markdown bundles inherit `<basename>` from the PDF — never hand-rename them; `pdf-to-markdown.py` derives the directory and `.md` filename from `Path.stem`. If you discover the wrong PDF name only after running Step 7, rename **the PDF**, then re-run with `--force`.
- Metadata JSON: `raw/<slug>_metadata.json`. Fulltext JSON: `raw/<slug>_fulltext.json`.
- Reports: always `report.md` and `report_zh.md`.
- **First-author surname must come from the landing page** (Step 5).

## Verification bar

- State **in silico** vs **wet-lab validated** for every numerical claim.
- Flag **reviews / perspectives** explicitly.
- Tag `[search-only, unverified]` claims.
- If source is a company blog, find the underlying paper first.

## Red flags — STOP and fix before finishing

- [ ] PDF in `papers/` but report body only mentions it in a citation row.
- [ ] PDF in `papers/` but no matching bundle in `markdown/<basename>/`. Run `pdf-to-markdown.py`.
- [ ] `markdown/_index.json` records fewer entries than `papers/*.pdf`.
- [ ] `report_zh.md` doesn't exist or isn't structurally parallel.
- [ ] Numerical claim missing in-silico-vs-wet-lab qualifier.
- [ ] PDF filename with spaces or non-ASCII characters.
- [ ] DOI or arXiv ID duplicates a prior run (dedupe broke).
- [ ] Company blog cited without link to primary paper.
- [ ] Playwright browser left open after the run.
- [ ] `raw/<slug>_pdf_b64.json` intermediates still on disk after decode.

## File inventory

| File | Purpose |
|---|---|
| `SKILL.md` (this file) | Authoritative workflow — self-contained |
| `scope.md` | Default priority areas + venue rankings |
| `report-template.md` | English report skeleton |
| `report-template-zh.md` | Chinese report skeleton |
| `playwright-extract.js` | Paste into `browser_evaluate` — extracts DOI/authors/abstract/pdf_url |
| `playwright-fetch-pdf.js` | Paste into `browser_evaluate` — bioRxiv-compatible PDF fetch with base64 return |
| `pdf-to-markdown.py` | PyMuPDF + markitdown converter. Step 7 of the workflow. CLI: `--out OUT INPUT...`. Idempotent; pass `--force` to redo. Shared with the Claude Code and Opencode port copies of this skill. |
