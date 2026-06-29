# Shared arXiv site chrome (header + announcement + footer)

Engineering notes for the shared public-page chrome. These notes used to live as
comments inside `arxiv/base/static/css/arxiv-header-footer.css`; they were moved
here because CSS comments are served to end users and this documentation should
not be distributed in the shipped asset.

The chrome is three assets in `arxiv/base/static/`, published to GCS (see the
"Publishing static files to GCS" section of the top-level `README.md`):

- `css/arxiv-header-footer.css` — the stylesheet (this document describes it).
- `js/arxiv-header.js` — behavior (search overlay, hamburger, banner dismissal,
  institutional acknowledgement).
- `templates/base/header.html`, `footer.html`, `announcement_banner.html` — the
  markup that consumes the classes below.

## Provenance and sync policy

The stylesheet is a **self-contained subset** extracted from the arXiv design
system (`design-patterns/public/design-system.css`, the approved `.ds-*`
components). It is the single chrome stylesheet arxiv-base owns; arxiv-submit
vendors it, and browse/auth/search consume it via arxiv-base.

It contains only the chrome — `.ds-announcement`, `.ds-skip-link`,
`.ds-site-header` (+ hamburger), `.ds-site-footer`, `.ds-nav-icon` — plus the
`--arxiv-*` tokens those rules reference (1:1 with the canonical names/values).

**Re-sync from the design system when the components change; do not hand-edit
the component rules.** The `:root` token block is the canonical subset — keep
names and values identical to design-system.css.

### Self-hosted IBM Plex Sans

design-system.css references the family but ships no `@font-face` (it assumes the
host provides the fonts); this bundle self-hosts it. The `@font-face` `src` paths
are relative to the stylesheet (`static/css` → `../fonts`).

### Interop with legacy host stylesheets

Two rules exist purely to win specificity battles with legacy host CSS (e.g.
browse's `arXiv.css`). Do not "simplify" them away:

- `.ds-site-footer a, …:hover, …:active { border-bottom: 0 }` neutralizes the
  legacy `footer a:hover { border-bottom: 1px dotted }` so it doesn't stack a
  dotted underline on chrome footer links (must beat `footer a:hover` = 0,0,1,2).
- `.ds-announcement .ds-announcement-link` is scoped under `.ds-announcement`
  (specificity 0,0,2,0) so it beats a legacy reset like
  `a:link,a:visited,a:active{text-decoration:none;font-weight:normal}` (0,0,1,1)
  that would otherwise strip the underline + bold.

The `.is-sr-only` utility is included self-contained so the chrome's "(opens in
new tab)" hint stays visually hidden even when the host's arXiv.css /
arxivstyle.css is absent.

## Site footer (`.ds-site-footer`)

The universal arXiv public-page footer. Design approved 2026-06-11, validated in
three places that agree almost exactly: the approved spinout-header-footer Cloud
Run deployment, `mockups/abstract-redesign.html`, and `mockups/html-redesign.html`
("the most validated component on this list" — `audits/2026-06-11/AUDIT-COMPONENTS.md`).

Three pieces:

1. **Acknowledgment line** — "We gratefully acknowledge support from our **major
   funders**, **member institutions**, and all contributors." An optional inline
   institutional mention (IP-matched) follows "member institutions".
2. **Footer nav** — About · Help · Contact · Subscribe · Copyright · Privacy ·
   Accessibility · Operational Status, dot-separated.
3. **Funders column** — "Major funding support from" + Simons + Schmidt wordmark
   logos, right-aligned; drops below the main column at narrow widths.

Markup contract:

```html
<footer class="ds-site-footer">
  <div class="ds-site-footer-grid">
    <div class="ds-site-footer-main">
      <div class="ds-site-footer-ack">We gratefully acknowledge … </div>
      <nav class="ds-site-footer-links" aria-label="Site navigation">
        <a href="…">About</a>
        <span class="ds-site-footer-sep" aria-hidden="true">&middot;</span>
        …
      </nav>
    </div>
    <div class="ds-site-footer-funders">
      <div class="ds-site-footer-funders-label">Major funding support from</div>
      <div class="ds-site-footer-funders-logos">
        <img class="ds-funder-logo" src="…" alt="Simons Foundation">
        <img class="ds-funder-logo" src="…" alt="Schmidt Sciences">
      </div>
    </div>
  </div>
</footer>
```

Accessibility notes (the behavior contract travels with the pattern):

- Real `<footer>` landmark; nav has `aria-label="Site navigation"`.
- Dot separators carry `aria-hidden="true"` (screen readers otherwise announce
  "middot" between every link).
- Funder logos carry real alt text (organization names).
- External links (Operational Status) need `target="_blank"` +
  `rel="noopener noreferrer"` + sr-only "(opens in new tab)".
- Type sizes in `rem` so user font-size overrides propagate.
- `.ds-funder-logo` uses `box-sizing: content-box` so `height: 40px` describes the
  image content height — with the global `border-box`, padding + border would
  shrink the logo to ~30px (visibly small vs the approved layout).

## Site header unit (`.ds-announcement` + `.ds-site-header`)

The universal arXiv public-page header. Design approved 2026-06-11, validated
against the spinout-header-footer Cloud Run deployment (reference implementation:
`mockups/abstract-redesign.html`).

This is **one pattern with two stacked pieces**, codified together because the
approved deployment treats them as a unit:

1. **`.ds-announcement`** — dismissable light-blue announcement band. Render only
   while an announcement is active; the close button persists dismissal
   (localStorage in production, keyed by `data-banner-name`).
2. **`.ds-site-header`** — the black bar (Repository Brown `#1c1a17`, phase-2
   spinout brand): logo left, nav right (Search / Submit / Donate | Log in).

A third piece, a breadcrumb band, was briefly part of this pattern and **removed
2026-06-11** — at 2 levels deep it doesn't justify the real estate, and its links
are available elsewhere (header logo = home; Subjects in the abstract metadata =
category listing). The approved deployment covers only the banner and the black
bar.

Markup contract (abridged):

```html
<a class="ds-skip-link" href="#main">Skip to main content</a>
<div class="ds-announcement" role="region" aria-label="Announcement">
  <img class="ds-announcement-glyph" src="…" alt="" aria-hidden="true">
  <span class="ds-announcement-text">…</span>
  <a class="ds-announcement-link" href="…">Learn more</a>
  <button type="button" class="ds-announcement-close"
          aria-label="Dismiss announcement">&times;</button>
</div>
<header class="ds-site-header">
  <a href="/" class="ds-site-header-logo" aria-label="archive home">
    <img src="…" alt="archive">
  </a>
  <nav class="ds-site-header-nav" aria-label="Main navigation">
    <a href="/search" id="…">…Search</a>
    <a href="/submit">Submit</a>
    <a href="…">Donate</a>
    <span class="ds-site-header-divider" aria-hidden="true"></span>
    <a href="/login" class="ds-site-header-login">Log in</a>
  </nav>
</header>
```

Behavior contract (travels with the pattern):

- The skip link (`.ds-skip-link`) is the FIRST focusable element on the page,
  visible only on keyboard focus.
- Logo alt text and aria-labels say "archive" — the spoken form of "arXiv".
- The Search control is an `<a href="/search">` that JS may upgrade to open a
  search overlay (`preventDefault`). Never a dead button: without JS it navigates
  to the search page.
- Focus rings on the dark bar use `--arxiv-focus-ring-dark` (`#64b5f6`) — the
  standard Link Blue ring is invisible against `#1c1a17`.
- `--arxiv-grey-dis` nav text on `#1c1a17` is 7.4:1 — passes AA on dark.
- The announcement close button needs a persisted dismissal in production; the
  banner is temporal — page function must not depend on it (newcomer signposting
  needs a permanent home; open design question).

### Non-sticky header

The header is intentionally **not** sticky (decided 2026-06-11): it scrolls away
like any other content. Sticky chrome is exceptional at arXiv ("Chrome and
interaction structure"); only the HTML reader's header earns it. Static
positioning also returns the bar's height to the mobile viewport and removes the
anchor-offset hazard class from every page using this pattern.

### Responsive nav / hamburger

Below 599px the bar wraps the full nav to a second row — WCAG 1.4.10 reflow,
verified at 320px (no horizontal scroll). **This is the baseline** (incl. no-JS,
any browser); visible labels keep voice-control users working.

`arxiv-header.js` opts INTO the hamburger by adding `.is-collapsible` to
`.ds-site-header`; the CSS hides the toggle until that class is present. Because
the same script adds the class AND wires the toggle, the hamburger appears only
when it actually works — nothing is gated on a global "js" class. The QA name for
this treatment is the "<599px phone hamburger" (ARXIVCE-4426).

Behavior contract: host JS adds `.is-collapsible` to `.ds-site-header`, toggles
`.is-open` on `.ds-site-header-nav`, and keeps `aria-expanded` in sync on the
toggle (reference impl: `arxiv-header.js`). The collapsed dropdown is a clean
stacked list (flush full-width rows separated by hairlines), dropped below the
52px bar and absolutely positioned (the header is non-sticky) at `z-index: 60`.

## Search overlay (browse-local progressive enhancement)

`.arxiv-search-overlay` / `.arxiv-search-panel` are a progressive enhancement
layered on the design-system `<a href="/search">` Search control: `arxiv-header.js`
intercepts the click and opens this in-page overlay. Not part of design-system.css
yet — a candidate to upstream. Uses only the `--arxiv-*` tokens defined in the
`:root` subset.
