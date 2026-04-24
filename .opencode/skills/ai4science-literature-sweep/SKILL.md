---
name: ai4science-literature-sweep
description: Find, download, and summarize recent AI-for-science research (molecules, enzymes, soft materials, protein language models, polymers, foundation models, autonomous labs). Run periodic AI4Science literature updates into a dated folder with primary-source PDFs and a bilingual report. Not available when opencode uses a non-OpenCode provider without OPENCODE_ENABLE_EXA=1 (websearch tool required).
---

# AI4Science literature sweep (Opencode)

One invocation produces one dated folder in the current working directory containing: a bilingual narrative summary report (English + Chinese, structurally parallel), primary-source PDFs downloaded via curl, bibliographic metadata, and a dedupe-aware record of what was covered.

## Output contract — non-negotiable

```
$PWD/YYYY-MM-DD/
├── report.md         English narrative — required
├── report_zh.md      Chinese narrative — required, structurally parallel to report.md
├── papers/           Downloaded PDFs, <FirstAuthor><Year>_<slug>.pdf, ASCII only
└── raw/              Metadata dumps and full-text extractions
```

`YYYY-MM-DD` = today's date. **Both report files are mandatory in every run.** Nothing goes in the root of `$PWD`.

## Prerequisites

- `websearch` tool: requires `OPENCODE_ENABLE_EXA=1` env var (or OpenCode provider). Without it, skip websearch and use `webfetch` directly on known URLs (arXiv, DOI resolver) for discovery. This is much slower — prefer the env var.
- No Playwright / browser automation is available in opencode. All downloads use `curl` via `bash`. JS-rendered journal pages (Nature, ACS, RSC) and Cloudflare-protected sites (bioRxiv) have limited or no PDF access.

## Workflow — 8 steps, in order

1. **Load scope.** Read the sibling `scope.md` for the four priority areas (molecules / enzymes / soft materials / cross-cutting) and venue rankings. If `$PWD/.ai4science-scope.md` exists, it overrides.

2. **Dedupe prior runs.** Compute the set of DOIs and arXiv IDs already covered:
   ```
   grep -hrE '10\.[0-9]{4,}/[^ )]+|arXiv:[0-9]{4}\.[0-9]+' $PWD/*/report.md 2>/dev/null \
     | grep -oE '(10\.[0-9]{4,}/[^ )]+|arXiv:[0-9]{4}\.[0-9]+)' | sort -u
   ```
   Any hit matching an ID in this set is skipped.

3. **Create today's folder.** `mkdir -p $PWD/YYYY-MM-DD/papers $PWD/YYYY-MM-DD/raw`.

4. **Discover.** Run `websearch` if available (one search per priority area in a single message). If `websearch` is unavailable, use `webfetch` to query arXiv search: `https://arxiv.org/search/?query=<encoded terms>&searchtype=all&start=0`. Restrict to current + previous calendar year. Rank: peer-reviewed > preprint, primary > review.

5. **Verify first-author surnames from landing pages before naming anything.** The authoritative source is the landing page's `citation_author[0]` meta tag. Use `webfetch` on the arXiv abstract page (`https://arxiv.org/abs/<id>`) — arXiv serves `citation_author` in static HTML, no JS needed. For DOI-based papers, use `webfetch` on `https://doi.org/<doi>` (redirects to the publisher page; check the returned content for author info).

6. **Download — only curl available.** Full decision table:

   | Source | Method | Why |
   |---|---|---|
   | arXiv | `curl -L --fail --max-time 60 -o papers/<name>.pdf https://arxiv.org/pdf/<id>` | No bot protection |
   | PMC / ChemRxiv / OA journals | Same curl with `-A "Mozilla/5.0 ..."` | Most OA PDFs work |
   | Nature Commun. / npj / Science Advances OA | curl with UA on `https://www.nature.com/articles/<id>.pdf` | Works when OA |
   | Nature / Science / ACS / RSC / Cell (non-OA) | **Metadata only** — mark "closed access / no Playwright available" in the report | JS-rendered pages need Playwright |
   | bioRxiv | **Metadata only** — skip or note "Cloudflare blocked, no Playwright" | curl returns 403; cf_clearance is httpOnly |
   | Any curl failure | Save the abstract via webfetch into `raw/<slug>_fulltext.txt` as grounding | Avoid empty citations |

7. **Read what was downloaded.** Use `read` on PDF paths. If opencode's `read` cannot extract PDF text (binary output), use `bash` with `pdftotext` (if available) or fall back to the abstract / fulltext saved in `raw/`. The rule: every paper in `papers/` must contribute paper-specific content to `report.md` — actual methods, numerical results, limitations. If you can't read the PDF, download fewer papers but read each one you keep.

8. **Write both reports in parallel structure.** Use `report-template.md` and `report-template-zh.md` as scaffolds. Four sections (one per priority area). Translate idiomatically for Chinese version. End with "Reading-priority recommendation", "Local downloads" table, and "Caveats / known gaps".

## Grounding discipline — the load-bearing rule

Every bullet must be backed by one of these, in order:
1. **The paper's PDF read this run** — highest weight.
2. **Abstract or fulltext in `raw/`** — cite the file in the downloads table.
3. **`websearch` snippet** — allowed for discovery pointers to next-run targets; tag every such bullet `[search-only, unverified]`.

A claim about a specific numerical result must come from category 1 or 2. **Never launder a search-snippet number without the tag.**

## Filename discipline

- PDFs: `<FirstAuthorLastName><Year>_<short-slug>.pdf`. ASCII only, no spaces. Append `_preprint` for arXiv / bioRxiv. Example: `Kim2025_g2d-diff_cancer-small-mol_preprint.pdf`.
- Metadata: `raw/<slug>_metadata.json`. Fulltext: `raw/<slug>_fulltext.txt`.
- Reports: always exactly `report.md` and `report_zh.md`.
- **First-author surname must come from `webfetch` of the abstract page** (Step 5). Never guess from DOI or URL.

## Verification bar

- State **in silico** vs **wet-lab validated** for every numerical claim.
- Flag **reviews / perspectives** explicitly.
- Tag `[search-only, unverified]` claims and list them under "to verify next run".
- If a source is a company blog, find the underlying paper — don't cite the blog as primary.

## Common mistakes — rationalization check

| If you're thinking… | Reality |
|---|---|
| "I'll just list the paper in the table for now" | That IS the grounding failure. Read now or don't download. |
| "The curl error on bioRxiv means I can't cite it" | You can cite it with metadata-only, but mark it clearly in the report. |
| "The first-author surname is probably 'X' from the URL" | It almost certainly isn't. webfetch the abstract page. |
| "English report is enough for a quick run" | No. Both `report.md` and `report_zh.md` are required. |
| "I can put output next to the project root" | No. Nest under `YYYY-MM-DD/`. |
| "Playwright is safer, I'll wish I had it" | Opencode doesn't have Playwright. Use curl; accept the metadata-only limits for JS-heavy sites. |

## Red flags — STOP and fix before finishing

- [ ] A paper's PDF is in `papers/` but the report body only mentions it in a citation row.
- [ ] `report_zh.md` doesn't exist or isn't structurally parallel to `report.md`.
- [ ] Any numerical claim missing the in-silico-vs-wet-lab qualifier.
- [ ] Any PDF filename with spaces or non-ASCII characters.
- [ ] A DOI or arXiv ID also appears in a prior `YYYY-MM-DD/report.md` (dedupe broke).
- [ ] A cited source is a company blog without a link to the primary paper.
- [ ] `raw/<slug>_pdf_b64.json` intermediates left on disk (not applicable — no Playwright, but check for other intermediates).

## File inventory

| File | Purpose |
|---|---|
| `SKILL.md` (this file) | Authoritative workflow — self-contained |
| `scope.md` | Default priority areas + venue rankings |
| `report-template.md` | English report skeleton |
| `report-template-zh.md` | Chinese report skeleton |
