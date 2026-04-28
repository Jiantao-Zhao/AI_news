#!/usr/bin/env python3
"""pdf-to-markdown.py — Convert downloaded PDFs into markdown bundles.

Layout produced (one bundle per input PDF):

    <out>/<basename>/
        <basename>.md          # figure index + page anchors + body text
        figures/
            p<NN>_img<MM>.png  # embedded images
            p<NN>_page-render.png  # full-page raster fallback for figure-heavy vector pages
    <out>/_index.json          # summary record across the run

Heuristics:
- Each embedded image is exported via fitz.Pixmap (CMYK auto-converted to RGB).
- A page with NO embedded images but ≥ VECTOR_THRESHOLD vector drawing paths is
  rasterized at 150 DPI as a single "page-render" PNG. This recovers chart-heavy
  vector pages (typical of Nature/Science/Phys Rev figures) that would otherwise
  be invisible to downstream readers.
- Body text is extracted with `markitdown` (Microsoft) which preserves more
  structure than raw PyMuPDF text. If markitdown fails, falls back to PyMuPDF.

Idempotent: an existing bundle with a non-empty .md is skipped unless --force.

Run via the skill's bundled venv:
    ~/.claude/skills/ai4science-literature-sweep/.venv/bin/python \\
        ~/.claude/skills/ai4science-literature-sweep/pdf-to-markdown.py \\
        --out 2026-MM-DD/markdown 2026-MM-DD/papers
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import fitz  # PyMuPDF

try:
    from markitdown import MarkItDown
    _MD = MarkItDown()
except Exception:  # noqa: BLE001
    _MD = None

VECTOR_THRESHOLD = 50          # vector-path count to trigger page-render fallback
RENDER_DPI = 150


def process_pdf(pdf_path: pathlib.Path, out_root: pathlib.Path, force: bool = False) -> dict:
    base = pdf_path.stem
    bundle = out_root / base
    md_path = bundle / f"{base}.md"
    fig_dir = bundle / "figures"

    if md_path.exists() and md_path.stat().st_size > 0 and not force:
        return {
            "pdf": pdf_path.name,
            "md": str(md_path.relative_to(out_root.parent)) if out_root.parent in md_path.parents else str(md_path),
            "skipped": True,
            "md_chars": md_path.stat().st_size,
        }

    fig_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    rows: list[tuple[int, str, str, int, int]] = []
    embedded_n = 0
    rendered_n = 0

    for pi, page in enumerate(doc, start=1):
        # 1) embedded images
        try:
            imgs = page.get_images(full=True)
        except Exception:
            imgs = []
        for ii, info in enumerate(imgs, start=1):
            xref = info[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha >= 4:  # CMYK → RGB
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                fname = f"p{pi:03d}_img{ii:02d}.png"
                pix.save(str(fig_dir / fname))
                rows.append((pi, fname, "embedded", pix.width, pix.height))
                embedded_n += 1
            except Exception as e:  # noqa: BLE001
                sys.stderr.write(f"  ! embed fail p{pi} img{ii}: {e}\n")
            finally:
                pix = None

        # 2) full-page render fallback
        try:
            n_paths = len(page.get_drawings())
        except Exception:
            n_paths = 0
        if not imgs and n_paths >= VECTOR_THRESHOLD:
            zoom = RENDER_DPI / 72.0
            mat = fitz.Matrix(zoom, zoom)
            try:
                pix = page.get_pixmap(matrix=mat, alpha=False)
                fname = f"p{pi:03d}_page-render.png"
                pix.save(str(fig_dir / fname))
                rows.append((pi, fname, "page-render", pix.width, pix.height))
                rendered_n += 1
            except Exception as e:  # noqa: BLE001
                sys.stderr.write(f"  ! render fail p{pi}: {e}\n")

    # 3) body text
    if _MD is not None:
        try:
            body = _MD.convert(str(pdf_path)).text_content
        except Exception as e:  # noqa: BLE001
            body = (
                f"(markitdown failed: {e}; falling back to PyMuPDF text)\n\n"
                + "\n\n".join(p.get_text() for p in doc)
            )
    else:
        body = "\n\n".join(p.get_text() for p in doc)

    # 4) compose markdown
    lines = [
        f"# {base}",
        "",
        f"**Source PDF:** `{pdf_path.name}`  ",
        f"**Pages:** see PyMuPDF page anchors below  ",
        f"**Embedded images extracted:** {embedded_n}  ",
        f"**Page renders (figure-heavy vector pages):** {rendered_n}",
        "",
        "---",
        "",
        "## Figure index",
        "",
        "| Page | File | Kind | W×H |",
        "|---|---|---|---|",
    ]
    for (pi, fn, kind, w, h) in rows:
        lines.append(f"| {pi} | [`{fn}`](figures/{fn}) | {kind} | {w}×{h} |")
    lines += ["", "---", "", "## Text (markitdown)", "", body, ""]

    md = "\n".join(lines)
    md_path.write_text(md, encoding="utf-8")
    doc.close()

    return {
        "pdf": pdf_path.name,
        "md": str(md_path.relative_to(out_root.parent)) if out_root.parent in md_path.parents else str(md_path),
        "n_figures": embedded_n + rendered_n,
        "embedded": embedded_n,
        "page_render": rendered_n,
        "md_chars": len(md),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="PDF files or directories of PDFs")
    ap.add_argument("--out", required=True, help="output root (creates <out>/<basename>/...)")
    ap.add_argument("--force", action="store_true", help="re-process even if a bundle already exists")
    args = ap.parse_args()

    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    pdfs: list[pathlib.Path] = []
    for inp in args.inputs:
        p = pathlib.Path(inp)
        if p.is_file() and p.suffix.lower() == ".pdf":
            pdfs.append(p)
        elif p.is_dir():
            pdfs.extend(sorted(p.glob("*.pdf")))
        else:
            sys.stderr.write(f"skip (not a pdf or dir): {p}\n")

    if not pdfs:
        sys.stderr.write("no PDFs to process\n")
        return 1

    if _MD is None:
        sys.stderr.write("WARNING: markitdown not importable; using PyMuPDF text fallback\n")

    index: list[dict] = []
    for pdf in pdfs:
        sys.stderr.write(f"[+] {pdf.name}\n")
        rec = process_pdf(pdf, out, force=args.force)
        if rec.get("skipped"):
            sys.stderr.write(f"    skip (bundle exists; use --force to redo)\n")
        else:
            sys.stderr.write(
                f"    {rec.get('embedded', 0)} embedded + "
                f"{rec.get('page_render', 0)} rendered, md {rec.get('md_chars', 0):,} chars\n"
            )
        index.append(rec)

    (out / "_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    sys.stderr.write(f"[done] {len(index)} record(s) → {out}/_index.json\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
