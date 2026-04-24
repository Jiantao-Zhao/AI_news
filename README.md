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

Each run produces a dated folder with bilingual reports and downloaded PDFs.
