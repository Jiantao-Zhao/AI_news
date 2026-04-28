# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Primary workflow

The workspace's entire sweep workflow is packaged as a reusable skill: **`ai4science-literature-sweep`**. When the user asks for a literature sweep, AI4Science news update, or a periodic run, invoke that skill. It is self-contained — defines folder layout, download discipline, bilingual-report requirement, PDF-grounding rule, and the `CronCreate` pattern for scheduled runs. The notes below are workspace-specific context layered on top of the skill; they don't replace it.

**Two copies of the skill exist** — both must stay in sync:
- **Project-level (authoritative for this workspace):** `./.claude/skills/ai4science-literature-sweep/` — travels with the project, survives if the global copy is lost, and guarantees any Claude session opened in this directory sees the skill even on a fresh machine.
- **Global (cross-project convenience):** `~/.claude/skills/ai4science-literature-sweep/` — so the skill is also usable from outside this workspace (e.g. if the user starts a second AI_news directory elsewhere).

When editing the skill, update **both** copies and verify with `diff -r ~/.claude/skills/ai4science-literature-sweep ./.claude/skills/ai4science-literature-sweep`. If they diverge, the project-level copy wins for this workspace.

**Ports for other platforms — same sync discipline:**

- **Opencode skill** — `./.opencode/skills/ai4science-literature-sweep/` (project) ↔ `~/.config/opencode/skills/ai4science-literature-sweep/` (global)
- **OpenClaw skill** — `./.agents/skills/ai4science-literature-sweep/` (project) ↔ `~/.agents/skills/ai4science-literature-sweep/` (global)

Both follow the same pattern: edit the project-level copy, mirror to global, verify with `diff -r`.

## What this workspace is

Not a codebase — a personal research-tracking workspace for the user (a scientist at Radboud University, `jiantao.zhao@ru.nl`) to follow **AI for Science** literature. Expect Markdown notes, downloaded papers, and occasional small analysis scripts — not an application.

**Scope priorities (in order):**
1. **AI for molecules** — generative models for small-molecule / ligand design, diffusion & flow-matching models, molecular property prediction, retrosynthesis, drug discovery.
2. **AI for enzymes / proteins** — protein language models (ESM-3, ProGen, ZymCTRL), structure prediction (AlphaFold family, RoseTTAFold), de novo enzyme design, ML-guided directed evolution.
3. **AI for soft materials** — polymers, self-assembly, coarse-grained MD + ML, inverse design of rheological / mechanical properties, shape-memory and stimuli-responsive materials.
4. Broader AI4Science foundation models and agentic / autonomous-lab systems when they intersect the above.

Deprioritize: generic LLM news, business/funding stories, tooling without scientific substance.

## Folder convention (run outputs)

Every literature sweep or news roundup produces **one dated folder** at the repo root:

```
YYYY-MM-DD/
├── report.md          # narrative summary in English — required
├── report_zh.md       # Chinese translation of report.md — required (user is a Chinese speaker)
├── papers/            # downloaded PDFs, named <firstAuthor><Year>_<slug>.pdf
├── markdown/          # auto-derived from papers/ via the skill's pdf-to-markdown.py — required
│   ├── _index.json    # one record per PDF: {pdf, md, n_figures, embedded, page_render, md_chars}
│   └── <basename>/<basename>.md  + figures/  (1:1 with papers/<basename>.pdf)
├── raw/               # raw HTML/JSON snapshots, search result dumps, screenshots
└── metadata.json      # optional: machine-readable index of papers/ entries
```

After every download batch, the skill runs `pdf-to-markdown.py` (PyMuPDF + markitdown, in the skill's bundled `.venv`) so each PDF gets a paired markdown bundle with a figure-index table at the top. Read the bundle's `.md`, not the raw PDF, when grounding the report — it loads faster and the figure index is right at the top.

**Both `report.md` and `report_zh.md` are required per run.** Keep them structurally parallel (same section headings, same paper ordering, same tables) so the user can cross-reference. Write each version idiomatically rather than as a literal translation — technical terms follow Chinese scientific convention (e.g. "扩散模型", "流变学逆向设计", "湿实验"), citations and file names stay in ASCII.

Never write today's output to the repo root — always nest it inside the dated folder. The prior-day survey at `2026-04-22/report.md` is the reference layout.

Keep `report.md` under ~500 lines; if a single sweep produces more, split into `report_molecules.md`, `report_enzymes.md`, etc. under the same dated folder.

## Collecting sources — how to fetch

There are three layered tools for getting material into `raw/` and `papers/`. Use the lightest one that works; escalate only on failure.

1. **WebSearch** — discovery only. Cheap, no download. Use it to generate the list of candidate URLs. Always run topic searches **in parallel** (one tool call per priority area in a single message).
2. **Bash + `curl`** — preferred for static downloads: arXiv PDFs (`https://arxiv.org/pdf/<id>`), bioRxiv / ChemRxiv PDFs, NIH PMC OA PDFs. One command per paper, saved into `papers/`. Set `-L` to follow redirects and `--fail` so bad URLs error rather than save an HTML error page.
3. **Playwright MCP** (`mcp__plugin_playwright_playwright__*`) — when a real browser is required: JavaScript-rendered journal pages (Nature, Science, Cell, ACS, RSC), pages behind cookie walls, PDF links hidden inside interactive tabs, or when the user wants a screenshot / accessibility snapshot of the page. Save snapshots into `raw/` (use the `filename:` parameter on `browser_snapshot` / `browser_network_requests`). Always `browser_close` at the end of a session.

Do **not** try to bypass paywalls. If a paper is closed-access, capture the abstract + bibliographic metadata and note "closed access" in `report.md` — do not grab it from Sci-Hub or similar.

## File naming inside `papers/`

`<firstAuthorLastName><Year>_<short-slug>.pdf`, e.g. `Jumper2021_alphafold2.pdf`, `Hayes2025_esm3.pdf`. No spaces, ASCII only. If the paper is a preprint, append `_preprint`, e.g. `Zhang2026_enzyme-de-novo_preprint.pdf`.

## Source discipline

When searching for "latest research", prefer in this order:
1. **Peer-reviewed venues**: Nature family (Nature, Nat. Chem., Nat. Mach. Intell., Nat. Comm., npj Comput. Mater.), Science, Cell, JACS, ACS Central Science, PNAS, Soft Matter, Macromolecules, Chem. Sci.
2. **Preprint servers**: arXiv (`cs.LG`, `q-bio.BM`, `cond-mat.soft`, `physics.chem-ph`), bioRxiv, ChemRxiv.
3. **Conference proceedings**: NeurIPS (AI4Science / MLSB workshops), ICML, ICLR (MLDD), RECOMB, ISMB.

Restrict searches to the **current and previous year** (currently 2025–2026) unless the user asks for background. Always include publication year and venue — a claim without a venue is not usable.

## Verification bar

AI4Science press releases routinely overstate results. Before summarizing a claim:
- Distinguish **in silico prediction** from **wet-lab validated** (molecules synthesized, enzymes expressed, materials fabricated).
- Note dataset scale and whether baselines include a strong classical method, not only older ML.
- Flag reviews and perspective pieces explicitly — they are not primary results.

If a source is a company blog or news aggregator, find the underlying paper before citing.

## Scheduled / periodic runs

The user wants this workspace updated on a recurring schedule via `CronCreate`. When a scheduled run fires, the prompt should be self-contained enough to re-enter the workflow without conversation context:

1. Compute today's date → create `YYYY-MM-DD/` with `papers/` and `raw/` subfolders.
2. Run parallel WebSearch across the priority areas, filtered to publications dated **since the previous run's folder date**.
3. For each top-ranked primary paper, download the PDF (`curl` for arXiv / PMC / bioRxiv, Playwright for JS-rendered journal pages) into `papers/`.
4. Write `report.md` following the established layout.
5. Skip any paper that duplicates one already present in an earlier dated folder (grep the prior folders' `report.md` for the DOI / arXiv ID before downloading).

Remind the user that Claude Code cron jobs from `CronCreate` live only in the session (or need `durable: true`) and auto-expire after 7 days — they may need renewing.

## MCP tools available

- **Playwright** (`mcp__plugin_playwright_playwright__*`) — browser automation for JS-heavy pages and PDF downloads.
- **Context7** (`mcp__plugin_context7_context7__*`) — up-to-date docs for libraries the user might touch: PyTorch, RDKit, DeepChem, JAX-MD, OpenMM, BioPython, etc. Prefer over WebSearch for library API questions.
