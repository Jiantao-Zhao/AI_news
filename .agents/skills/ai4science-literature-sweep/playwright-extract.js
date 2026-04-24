// Paste this into `mcp__plugin_playwright_playwright__browser_evaluate` as the `function` argument
// after navigating to a journal article landing page.
//
// Works tested on: nature.com, science.org (partial), pubs.acs.org (partial),
// pubs.rsc.org (partial), cell.com (partial).
// For Nature-family pages it extracts DOI, authors, abstract, and PDF URL reliably.
//
// Call with:  filename: "<YYYY-MM-DD>/raw/<slug>_metadata.json"
// so the returned JSON lands straight in the dated folder's raw/ subdir.

() => {
  const meta = {};
  const grab = (name) =>
    document.querySelector(`meta[name="${name}"]`)?.content ||
    document.querySelector(`meta[property="${name}"]`)?.content;

  meta.title =
    grab('dc.title') ||
    grab('citation_title') ||
    grab('og:title') ||
    document.title;

  meta.doi = grab('DOI') || grab('citation_doi') || grab('dc.identifier');

  meta.journal =
    grab('citation_journal_title') ||
    grab('prism.publicationName') ||
    grab('og:site_name');

  meta.date =
    grab('dc.date') ||
    grab('citation_publication_date') ||
    grab('article:published_time') ||
    grab('citation_online_date');

  meta.authors =
    Array.from(document.querySelectorAll('meta[name="dc.creator"]')).map(m => m.content);
  if (meta.authors.length === 0) {
    meta.authors = Array.from(document.querySelectorAll('meta[name="citation_author"]')).map(m => m.content);
  }

  // Try the common abstract containers in order of specificity.
  meta.abstract =
    document.querySelector('#Abs1-content p')?.innerText ||            // Nature family
    document.querySelector('section[data-title="Abstract"] p')?.innerText ||
    document.querySelector('div.abstract p')?.innerText ||             // ACS
    document.querySelector('section.article-section__abstract p')?.innerText || // Cell
    document.querySelector('#abstract-1 p')?.innerText ||              // RSC
    document.querySelector('meta[name="dc.description"]')?.content ||
    null;

  // Prefer explicit PDF-download links; fall back to any .pdf href.
  const pdfA =
    document.querySelector('a[data-track-action="download pdf"]') ||
    document.querySelector('a[data-test="download-pdf"]') ||
    document.querySelector('a.c-pdf-download__link') ||
    document.querySelector('a[href$=".pdf"]');
  meta.pdf_url = pdfA ? new URL(pdfA.href, location.href).href : null;

  meta.url = location.href;
  meta.access = grab('citation_access') ||
                (document.body.innerText.match(/open access/i) ? 'open' : 'unknown');

  return meta;
}
