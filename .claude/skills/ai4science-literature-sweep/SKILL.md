---
name: ai4science-literature-sweep
description: Use when the user asks to find, download, or summarize recent AI-for-science research (molecules, enzymes, soft materials, protein language models, polymers, foundation models, autonomous labs), or to run a periodic AI4Science news / literature update into a dated folder with primary-source PDFs and a bilingual report
---

# AI4Science literature sweep

One invocation produces one dated folder in the current working directory containing: a bilingual narrative summary report (English + Chinese, structurally parallel), primary-source PDFs downloaded end-to-end for every paper cited, structured bibliographic metadata, and a dedupe-aware record of what was covered. The skill is self-contained — everything needed to execute is in this file; the sibling files (`scope.md`, templates, JS helpers) are referenceable resources, not prerequisites.

## Output contract — non-negotiable

```
$PWD/YYYY-MM-DD/
├── report.md         English narrative — required
├── report_zh.md      Chinese narrative — required, structurally parallel to report.md
├── papers/           Downloaded PDFs, <FirstAuthor><Year>_<slug>.pdf, ASCII only
└── raw/              Landing-page metadata JSON, full-text extraction JSON, search dumps
```

`YYYY-MM-DD` = today's date in the user's local timezone. **Both report files are mandatory in every run.** Nothing goes in the root of `$PWD` — always nest under the dated folder. If any paper appears in `papers/` without grounded content in the report body, the run is incomplete.

## Workflow — 8 steps, in order

1. **Load scope.** Read `scope.md` in this skill's directory for the four default priority areas (molecules / enzymes / soft materials / cross-cutting) and venue rankings. If `$PWD/.ai4science-scope.md` exists, it overrides.

2. **Dedupe prior runs.** Compute the set of DOIs and arXiv IDs already covered:
   ```bash
   grep -hrE '10\.[0-9]{4,}/[^ )]+|arXiv:[0-9]{4}\.[0-9]+' $PWD/*/report.md 2>/dev/null \
     | grep -oE '(10\.[0-9]{4,}/[^ )]+|arXiv:[0-9]{4}\.[0-9]+)' | sort -u
   ```
   Any search hit matching an ID in this set is skipped. Rotate angle between runs — if yesterday's §1 used a binder/peptide paper, today's §1 should find small-molecule work.

3. **Create today's folder.** `mkdir -p $PWD/YYYY-MM-DD/papers $PWD/YYYY-MM-DD/raw`.

4. **Discover in parallel.** Issue **one WebSearch per priority area in a single assistant message** (four searches in one message, not sequential). Restrict to the current + previous calendar year. Rank candidates: peer-reviewed > preprint, primary research > review, novel target > benchmark retread.

5. **Verify first-author surnames from landing pages before naming anything.** This is non-negotiable and the #1 naming bug. The bioRxiv DOI and arXiv ID both encode nothing about authorship; URL slugs are unreliable. The authoritative source is the landing page's `citation_author[0]` meta tag. Two extraction routes:
   - **Nature / Science / ACS / RSC / Cell** landing pages: use Playwright navigate + `playwright-extract.js` in `browser_evaluate` with `filename: "raw/<slug>_metadata.json"`. Returns `authors[0]`, `citation_pdf_url`, full abstract.
   - **arXiv abstract page**: `citation_author` meta tags are on `https://arxiv.org/abs/<id>`. The first PDF page header also works once downloaded.

6. **Download — lightest tool that works. Escalate only on failure.** Full decision table:

   | Source | Path | Why |
   |---|---|---|
   | arXiv | **A** `curl -L --fail --max-time 60 -o papers/<name>.pdf https://arxiv.org/pdf/<id>` | No bot protection; UA optional |
   | PMC / ChemRxiv / OA journals | **A** with `-A "$UA"` (Mozilla string) | Most OA journals have guessable `<url>.pdf` patterns |
   | Nature Commun. / npj / Science Advances OA | **A** with UA — `https://www.nature.com/articles/<id>.pdf` | Works when page is OA |
   | Nature / Science / ACS / RSC / Cell landing page | **B** Playwright `browser_navigate` → `playwright-extract.js` in `browser_evaluate` → curl returned `pdf_url` with UA | Need JS render for metadata |
   | **bioRxiv** | **C** Playwright navigate → wait ~6 s for Cloudflare → `playwright-fetch-pdf.js` in `browser_evaluate` (uses `credentials: 'include'` to inherit cf_clearance) → python base64-decode | curl returns HTTP 403 even with UA; cf_clearance is httpOnly |
   | Any site where A / B / C all fail | **D** `browser_evaluate` to dump rendered `.article.fulltext-view` / `main` / `article` text to `raw/<slug>_fulltext.json` | Valid grounding source; note in report that grounding came from rendered text |
   | Closed-access paper | **E** Metadata + abstract only, mark "closed access" in the report, move on | Never route around paywalls (no Sci-Hub, no mirrors) |

   **Canonical Path C one-liner for bioRxiv** (after Playwright is past Cloudflare):
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

7. **Read every downloaded PDF before writing the report — no exceptions.** Use `Read` with `pages: "1-8"` (or more for long papers). The authoritative rule: every PDF in `papers/` must contribute paper-specific content to `report.md` — actual methods named in the paper, actual numerical results with units and context, actual limitations the authors flag. **Citation-row-only appearance is the defining grounding failure**: it means the narrative was built from search snippets, not from the literature that was downloaded. If time is short, download fewer PDFs — do not skip the read.

8. **Write both reports in parallel structure.** Use `report-template.md` and `report-template-zh.md` as scaffolds. Four sections (one per priority area), each with "What the paper does / Verified numbers / Non-obvious observations / Limitations flagged by the authors". Translate idiomatically (use Chinese scientific convention: "扩散模型", "流变学逆向设计", "湿实验验证", "预印本", "基础模型"); keep authors, DOIs, arXiv IDs, filenames, URLs in ASCII. End with a "Reading-priority recommendation", a "Local downloads" table, and a "Caveats / known gaps" section.

## Grounding discipline — the load-bearing rule

Every bullet in the narrative must be backed by one of these sources, in preference order:
1. **The paper's own PDF read this run** — highest weight, always preferred.
2. **The landing page's abstract or full-text extraction in `raw/`** — equivalent to reading the PDF for grounding purposes; cite the JSON file in the "Local downloads" table.
3. **WebSearch snippet** — allowed only for discovery pointers that lead to next-run targets; every such bullet must be tagged `[search-only, unverified]`.

A claim about a specific numerical result (×-fold, % identity, compound count, capacity, Kd) must come from category 1 or 2. **Never laundrer a search-snippet number into the body without the tag.** When two similar-looking numbers come from different quantities (e.g. "16× activity gain" vs "90× substrate-preference ratio"), keep them syntactically distinct — they are different measurements, not synonyms.

## Filename discipline

- PDFs: `<FirstAuthorLastName><Year>_<short-slug>.pdf`. ASCII only, no spaces, hyphens instead of underscores in the slug. Append `_preprint` for arXiv / bioRxiv / ChemRxiv. Example: `Singh2025_autonomous-enzyme-platform.pdf`, `Passaro2025_boltz2_preprint.pdf`.
- Metadata JSON: `raw/<slug>_metadata.json`. Full-text JSON: `raw/<slug>_fulltext.json`.
- Reports: always exactly `report.md` and `report_zh.md`. If content exceeds ~500 lines, split by topic (`report_molecules.md` + `report_molecules_zh.md`, etc.).
- **First-author surname must come from the landing page** (Step 5). If the download happens before the metadata extraction, the filename is a guess — rename once the true author is known, before writing the report.

## Verification bar

For every numerical or performance claim in the report:
- State whether it is **in silico prediction** (docking score, model-predicted affinity, ADMET score) or **wet-lab validated** (synthesized and characterized molecule, expressed and assayed enzyme, fabricated and measured material).
- Flag **reviews and perspectives** as such — they are not primary results.
- Tag **search-only, unverified** claims explicitly and list them under "to verify next run" at the end of the section.
- If a source is a company blog or news aggregator, find the underlying paper first — do not cite the blog as primary.

## Scheduled / periodic runs

When the user wants this on a recurring schedule, use `CronCreate` with a **self-contained prompt** that re-enters this skill. Parameters to confirm with the user before creating the cron:
1. **Frequency** (daily / weekly / 2× per week)
2. **Time of day** in user's local timezone — pick **off-zero minutes** (e.g. `7 * * * *`, not `0 * * * *`) to avoid the cache-miss cliff and fleet-synchronization hotspots.
3. **Durable vs session-only** — `durable: true` persists across restarts. Note that **all Claude Code crons auto-expire after 7 days**, so weekly renewal is needed regardless.
4. **Per-run paper budget** (recommended ≤4, one per priority area) to cap disk and time cost.
5. **Dedupe policy** — always on by default (Step 2).

## Common mistakes — rationalization check

| If you're thinking… | Reality |
|---|---|
| "I'll just list the paper in the table for now, I'll read it later" | That IS the grounding failure. Read now or don't download. |
| "The search snippet already gives the headline number, I can skip the PDF" | Search snippets misreport quantities. Always verify numerical claims against the primary source. |
| "The first-author surname is probably '<X>' from the URL" | It almost certainly isn't. DOI / arXiv IDs are chronological. Read `citation_author[0]`. |
| "curl returned 403 on bioRxiv, I'll skip this paper" | Expected behaviour — cf_clearance is httpOnly. Escalate to Path C; it works. |
| "English report is enough for a quick run" | No. Both `report.md` and `report_zh.md` are required every run. |
| "I can put today's output next to CLAUDE.md" | No. Nest under `YYYY-MM-DD/`. |
| "Playwright is safer, I'll use it for arXiv too" | Wasted time. curl is faster; Playwright is only needed for JS-rendered pages and Cloudflare-protected PDFs. |
| "This ×-fold claim is probably the same as the other ×-fold claim" | Often a different quantity (activity vs preference ratio, raw vs normalized). Keep them distinct. |

## Red flags — STOP and fix before finishing

- [ ] A paper's PDF is in `papers/` but the report body only mentions it in a citation or table row, with no paper-specific method / number / limitation in the narrative. **Top-priority failure mode.**
- [ ] `report_zh.md` doesn't exist or isn't structurally parallel to `report.md`.
- [ ] Any numerical claim missing the in-silico-vs-wet-lab qualifier, or any search-only claim missing the `[search-only, unverified]` tag.
- [ ] Any PDF filename with spaces, non-ASCII characters, or missing `<Author><Year>_` prefix.
- [ ] A DOI or arXiv ID in today's `report.md` also appears in a prior `YYYY-MM-DD/report.md` (dedupe broke).
- [ ] A cited source is a company blog or news aggregator without a link through to the primary paper.
- [ ] Playwright browser left open after the run (missed `browser_close`).
- [ ] `raw/<slug>_pdf_b64.json` intermediates still on disk after successful decode (should be cleaned up).

## Worked example — a representative run

A four-paper sweep with mixed sources, following the full workflow:

1. **Setup**: `mkdir -p 2026-04-24/papers 2026-04-24/raw`. Grep prior `*/report.md` for DOIs and arXiv IDs → dedupe set.
2. **Parallel WebSearch** (one message, four tool calls): `"diffusion model small molecule drug discovery 2026 wet-lab validated"` / `"Boltz-2 protein structure affinity 2026 bioRxiv primary"` / `"shape memory polymer machine learning inverse design 2026 RSC"` / `"autonomous chemistry laboratory LLM agent 2026 primary"`. Pick one primary per area.
3. **Metadata verification (Step 5)**: Playwright `browser_navigate` to the Nature Commun. landing page → `playwright-extract.js` → saves `raw/g2d-diff_metadata.json` → `authors[0]` = `"Kim, Hyunho"`. Filename locked in as `Kim2025_g2d-diff_cancer-small-mol.pdf`.
4. **Downloads — mixed paths**:
   - §1 G2D-Diff: **Path A** with UA. Nature Commun. PDF at `https://www.nature.com/articles/<id>.pdf`.
   - §3 Yan & Scalet SMP review: **Path A** with UA. RSC PDF pattern `https://pubs.rsc.org/en/content/articlepdf/<year>/<journal>/<doi-slug>`.
   - §4 ChatBattery: **Path A** (no UA needed). arXiv `https://arxiv.org/pdf/<id>`.
   - §2 Boltz-2: `curl` returns 403 on bioRxiv as expected. Escalate to **Path C** — navigate Playwright, wait 6 s for Cloudflare, `playwright-fetch-pdf.js` with `citation_pdf_url` from metadata, Python base64-decode, `file` sanity-check ("PDF document, version 1.5, 13 pages"), clean up intermediate JSON.
5. **Close Playwright** after both bioRxiv fetches and the metadata extraction are done.
6. **Read all four PDFs** with `Read` tool, `pages: "1-8"` each.
7. **Write `report.md`** with four sections, each containing specific methods and numbers extracted from the PDFs (e.g. "Boltz-2's Pearson correlation ~0.65 on the 4-target FEP+ subset", "ChatBattery's NMC-SiMg delivers 174 mAh/g vs NMC811's 135 mAh/g"). Flag in-silico-only results (e.g. G2D-Diff TNBC candidates had docking + MoA analysis only, no wet-lab synthesis).
8. **Write `report_zh.md`** with the same section structure, Chinese prose, ASCII citations.
9. **Verify** both files exist, parallel section counts match, no PDF is citation-row-only, dedupe didn't re-cover a prior paper.

Total tool calls for a 4-paper run: ~4 WebSearches, ~4 Playwright navigations (combinable), ~4 `browser_evaluate`, ~4–8 Bash (curl + decode), ~4 `Read`, 2 `Write`. Runs in one conversation turn sequence without context blowup.

## File inventory — this skill's directory

| File | Purpose |
|---|---|
| `SKILL.md` (this file) | Authoritative workflow — read this first. Self-contained. |
| `scope.md` | Default priority areas + venue rankings. Overridden by `$PWD/.ai4science-scope.md` if present. |
| `report-template.md` | English report skeleton (4 sections + reading-priority + downloads + caveats). |
| `report-template-zh.md` | Chinese report skeleton (structurally parallel). |
| `playwright-extract.js` | Paste into `browser_evaluate` with `filename:` — extracts DOI/authors/abstract/pdf_url from Nature-family and similar landing pages. |
| `playwright-fetch-pdf.js` | Paste into `browser_evaluate` with `filename:` — bioRxiv-compatible in-session PDF fetch with base64 return. Tested working. |
