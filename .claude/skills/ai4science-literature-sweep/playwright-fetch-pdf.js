// Paste into `mcp__plugin_playwright_playwright__browser_evaluate` after navigating to the
// article landing page (Playwright session must have already passed Cloudflare / bot-check).
// Call with:  filename: "<YYYY-MM-DD>/raw/<slug>_pdf_b64.json"
// Then decode with Bash (one-liner further below).
//
// Tested working on bioRxiv (Cloudflare-protected). The trick is `credentials: 'include'`
// so fetch() inherits the session's cf_clearance cookie — curl cannot replicate this
// because cf_clearance is httpOnly.
//
// REPLACE the `url` variable with the citation_pdf_url extracted by playwright-extract.js,
// OR with the known bioRxiv pattern: https://www.biorxiv.org/content/<doi>v<N>.full.pdf

async () => {
  const url = 'REPLACE_ME_WITH_CITATION_PDF_URL';

  const resp = await fetch(url, { credentials: 'include' });
  if (resp.status !== 200) return { error: `HTTP ${resp.status}`, final_url: resp.url };

  const buf = new Uint8Array(await resp.arrayBuffer());

  // Magic-byte sanity check — abort early if this isn't a PDF.
  const magic = new TextDecoder().decode(buf.slice(0, 5));
  if (!magic.startsWith('%PDF')) return { error: 'not a PDF', magic, size: buf.length };

  // btoa chokes on strings longer than ~2^17, so base64-encode in chunks.
  let bin = '';
  const CHUNK = 0x8000;
  for (let i = 0; i < buf.length; i += CHUNK) {
    bin += String.fromCharCode.apply(null, buf.subarray(i, i + CHUNK));
  }

  return {
    size: buf.length,
    content_type: resp.headers.get('content-type'),
    pdf_b64: btoa(bin),
  };
}

/* ─── Bash decode step (run AFTER browser_evaluate returns) ─────────────────
    python3 -c "
    import json,base64;
    d = json.load(open('YYYY-MM-DD/raw/<slug>_pdf_b64.json'));
    assert 'pdf_b64' in d, d;
    open('YYYY-MM-DD/papers/<FirstAuthor><Year>_<slug>.pdf','wb').write(base64.b64decode(d['pdf_b64']));
    print('wrote', d['size'], 'bytes')
    "
    file YYYY-MM-DD/papers/<FirstAuthor><Year>_<slug>.pdf      # sanity check
    rm YYYY-MM-DD/raw/<slug>_pdf_b64.json                       # clean up intermediate
────────────────────────────────────────────────────────────────────────────*/
