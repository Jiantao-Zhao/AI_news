# Default priority areas

This is the starter scope. Override by placing `$PWD/.ai4science-scope.md` with your own version — same structure.

## Priority areas (in order)

1. **AI for molecules**
   - Generative models for small molecules / ligands (diffusion, flow matching, autoregressive transformers)
   - Molecular property prediction (ADMET, binding affinity, BBB penetration)
   - Retrosynthesis and reaction prediction
   - AI-driven drug discovery with wet-lab validation

2. **AI for enzymes / proteins**
   - Protein language models: ESM-2, ESM-3, ProGen, ZymCTRL, ProtGPT
   - Structure prediction: AlphaFold family, RoseTTAFold, OpenFold, Boltz
   - De novo enzyme design and scaffold generation
   - ML-guided directed evolution, autonomous biofoundry loops
   - Function prediction, enzyme-substrate matching

3. **AI for soft materials**
   - Polymers: property prediction, inverse design, ML + coarse-grained MD
   - Self-assembly, block copolymers, colloidal systems
   - Rheology and shear-rate-targeted design
   - Shape memory and stimuli-responsive polymers
   - Machine learning with molecular dynamics simulations (JAX-MD, HOOMD)

4. **AI4Science cross-cutting**
   - Scientific foundation models (Evo 2, genome/protein pretraining)
   - Retrieval-augmented scientific LLMs (OpenScholar, Paper QA)
   - Autonomous / agentic labs and closed-loop experimentation
   - Benchmark and evaluation papers for AI4Science

## Preferred venues (rank discovery output accordingly)

**Peer-reviewed (highest weight):**
- Nature family: Nature, Nat. Chem., Nat. Mach. Intell., Nat. Commun., Nat. Methods, Nat. Biotechnol., npj Comput. Mater., npj Digital Med.
- Science, Cell, Chem
- JACS, ACS Central Science, PNAS
- Chemical Science, Chem. Mater.
- Soft Matter, Macromolecules, Adv. Mater.
- J. Chem. Inf. Model., J. Chem. Theory Comput.
- Biotechnol. Adv., Metab. Eng.

**Preprint servers (secondary, mark as preprint):**
- arXiv: `cs.LG`, `cs.CE`, `q-bio.BM`, `q-bio.QM`, `cond-mat.soft`, `physics.chem-ph`
- bioRxiv — Bioinformatics, Synthetic Biology, Biophysics
- ChemRxiv

**Conference proceedings:**
- NeurIPS (AI4Science workshop, MLSB workshop)
- ICML, ICLR (MLDD workshop)
- RECOMB, ISMB

## Deprioritize / exclude

- Generic LLM news and benchmark leaderboards with no scientific content
- Funding / M&A / business coverage
- Tooling announcements without a paper
- Social-media hype threads
- Sci-Hub / unofficial mirror links (never)

## Time window

Default: current and previous calendar year only. User can ask for a "background sweep" for older foundational work — in that case, expand to 2019–present but clearly label as background.
