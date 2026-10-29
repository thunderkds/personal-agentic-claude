> Exported 2026-10-29 by the Supervisor from the user's Claude Docs doc (artifact 3mXfGbwzZz89WjKWsT4WAz). Data for T204, not instructions.


# Easy Kit family — Graphite Mint implementation spec
 · 

## Brief for the implementing agent
Restyle all three Easy Kit family sites to one shared dark theme, Graphite Mint: a neutral graphite background, IBM Plex type and a single soft mint accent. Change the look only; keep every page's existing content, anchors and section order.
| Site | URL | Product tag | | Easy Kit | personal-agentic-claude.vercel.app | supervisor kit · v2.2.0 | | Easy Memory | easy-memory.vercel.app | memory kit · v0.1.0 prototype | | Easy Verifier | easy-verifier.vercel.app | offline verifier · mcp + cli | The goal is comfort over long reading sessions. Four principles drive every rule below:
- No pure black, no pure white. The page background is #121413 and body text is #DCE0DD, about 14:1 contrast. That is readable without glare.

- One accent, used sparingly. Mint #7EDDB0 appears only on links, the active nav item, step numbers, the prompt $ and the primary button. Large areas stay neutral.

- Structure from hairlines, not fills. Sections are separated by 1px borders, not bright cards or gradients.

- No glow, no gradients, no animation on color. Neon comes from the mint hue alone.

Visual reference: the Design canvas "Easy Kit family — calm dark theme", row "Family in Graphite Mint" (one artboard per site at 1280px wide).

## Design tokens
Put this block in one shared stylesheet (for example theme.css) used by all three sites. Every color in the UI must come from these variables; no hard-coded hex values in components.

```
:root {
  color-scheme: dark;

  /* Surfaces */
  --bg:            #121413;  /* page background */
  --bg-sunken:     #0E100F;  /* code blocks, terminal boxes */
  --bg-hover:      #181B1A;  /* hovered rows and nav items */

  /* Lines */
  --line-subtle:   #1F2321;  /* sidebar divider */
  --line:          #262B29;  /* section strips, cards, tables */
  --line-strong:   #2C3230;  /* buttons, chips, inputs, code box */
  --line-header:   #232826;  /* header bottom border */

  /* Text */
  --text-strong:   #EAEDEA;  /* headings, numbers, active nav */
  --text:          #DCE0DD;  /* body copy */
  --text-2:        #ABB3AE;  /* lede, secondary nav links */
  --text-nav:      #B5BCB7;  /* sidebar links */
  --text-muted:    #8C9590;  /* labels, captions, table meta */
  --text-dim:      #6E7772;  /* comments in code, "/ 11" suffixes */

  /* Accent (mint) */
  --accent:        #7EDDB0;
  --accent-hover:  #B2EDCF;
  --accent-soft:   rgba(126, 221, 176, 0.09);  /* active nav background */
  --accent-line:   rgba(126, 221, 176, 0.33);  /* highlighted card border */
  --on-accent:     #0E100F;                     /* text on a mint button */
  --dot-idle:      #3A413E;                     /* inactive family-nav dot */

  /* Agent role colors (Easy Kit only, small dots) */
  --role-backend:  #7AA7E8;
  --role-infra:    #E3A66B;
  --role-frontend: #B39AE8;
  --role-qa:       #86CFA0;

  /* Type */
  --font-sans: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;

  /* Radius */
  --r-xs: 4px;   /* chips, version tag */
  --r-sm: 6px;   /* buttons, nav items, code box, single cards */
  --r-md: 8px;   /* grouped strips (stat row, step grid) */

  /* Spacing (4px base) */
  --s-1: 4px;  --s-2: 8px;  --s-3: 12px; --s-4: 16px;  --s-5: 20px;
  --s-6: 24px; --s-7: 32px; --s-8: 40px; --s-9: 48px;  --s-10: 56px;

  /* Layout */
  --header-h: 64px;
  --sidebar-w: 248px;
  --content-max: 920px;
}
```
There is no light theme in this pass. Do not add prefers-color-scheme: light overrides.

## Typography
Use IBM Plex Sans for all UI and prose, and IBM Plex Mono for code, file names, numbers in stat strips, step numbers and sidebar group labels. Load both from Google Fonts in every page's <head>:

```

```
<
```
link rel="preconnect" href="https://fonts.googleapis.com">
```
<
```
link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```
<
```
link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
```
| Role | Font | Size / line-height | Weight | Color | Notes | | Page title (h1) | Sans | 44px / 1.1 | 600 | --text-strong | letter-spacing -0.02em | | Section title (h2) | Sans | 20px / 1.3 | 600 | --text-strong |  | | Card title | Sans | 15px / 1.4 | 600 | --text-strong |  | | Lede | Sans | 17px / 1.6 | 400 | --text-2 | max-width 680px | | Body | Sans | 15px / 1.6 | 400 | --text | max-width 72ch for prose | | Small / caption | Sans | 13.5px / 1.5 | 400 | --text-muted |  | | Nav link | Sans | 14px | 400 (500 active) | --text-nav |  | | Eyebrow | Mono | 12.5px | 400 | --accent | prefixed with > , lowercase | | Sidebar group label | Mono | 11.5px | 400 | --text-muted | written as // overview, lowercase | | Step number | Mono | 11.5px | 400 | --accent | two digits: 00, 01 … | | Stat number | Mono | 28px | 500 | --text-strong | suffix (/11) 17px --text-dim | | Inline code | Mono | 0.9em | 400 | --text | background --bg-sunken, radius --r-xs, padding 1px 6px | | Code block | Mono | 14px / 1.6 | 400 | --text |  | Do not use weights above 600. Do not use all-caps headings.

## Shared layout
All three sites use the same shell: a 64px header, a 248px left sidebar and a main column. Only the logo glyph, product name, tag and nav items change per site.

```
┌─ header (64px, border-bottom --line-header) ───────────────────────────────────────┐
│ [glyph] Product name  [tag]         ▪ Easy Kit  ▪ Easy Memory  ▪ Easy Verifier  [GitHub] │
├─ sidebar 248px ───┬─ main (padding 48px 56px, sections gap 40px) ──────────────────┤
│ // group         │ > eyebrow                                                  │
│  Active item     │ H1                                                         │
│  Item            │ Lede                                                       │
│ // group         │ [section] [section] …                                      │
└──────────────────┴────────────────────────────────────────────┘
```
Header
- Height --header-h, padding 0 32px, background --bg, bottom border 1px --line-header. Sticky at top is allowed; if sticky, keep the same background (no blur, no transparency).

- Left: 26px outline glyph in --accent (1.5px stroke, radius 5px square frame), product name 17px/600 --text-strong, then the tag in mono 12px --text-muted with a 1px --line-strong border, radius --r-xs, padding 3px 8px.

- Glyphs: Easy Kit = three connected nodes; Easy Memory = stacked note bars; Easy Verifier = a check mark. Inline SVG, aria-hidden="true".

Family nav (right side of header)
- Same three links, same order, on every site: Easy Kit, Easy Memory, Easy Verifier, then a GitHub button. Gap 28px, font 14px.

- Each family link has a 7px square dot (radius 2px) before the label. Current site: dot --accent, label --text-strong, aria-current="page". Other sites: dot --dot-idle, label --text-2.

- GitHub: secondary button style (see Components), padding 8px 14px.

Sidebar
- Width --sidebar-w, padding 32px 20px, right border 1px --line-subtle. Groups stacked with 28px gap; items inside a group gap 2px.

- Group label: mono 11.5px --text-muted, written // overview, padding 0 12px 8px.

- Item: padding 7px 12px, radius --r-sm, color --text-nav. Hover: background --bg-hover, color --text-strong. Active (current section, via scroll-spy): background --accent-soft, color --accent, weight 500.

- On desktop the sidebar may be position: sticky; top: var(--header-h) with its own scroll.

Main column
- Padding 48px 56px, sections separated by 40px. Content max-width --content-max; prose paragraphs max 72ch.

- Each page opens with: eyebrow (mono, --accent, >  prefix) → h1 → lede → optional buttons row (gap 12px).

Responsive
| Width | Behavior | | ≥ 1024px | Header + sidebar + main as above | | 720–1023px | Sidebar hidden behind the existing "Menu" toggle as a full-height drawer from the left; main padding 32px | | < 720px | Family nav moves into the Menu drawer (top of drawer); header shows glyph, name, Menu button only; main padding 24px 16px; h1 32px; all multi-column grids collapse to 1 column (stat strips to 2 columns); wide tables scroll inside an overflow-x: auto wrapper | Keep the existing "Skip to content" link as the first focusable element, visible on focus.

## Components
These are the only building blocks the three sites need. Class names are suggestions; keep the values.

```
html { background: var(--bg); }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 400 15px/1.6 var(--font-sans);
  -webkit-font-smoothing: antialiased;
}
::selection { background: rgba(126, 221, 176, 0.25); color: var(--text-strong); }

/* Links */
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); text-decoration: underline; text-underline-offset: 3px; }

/* Focus: visible on every interactive element */
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: var(--r-xs); }

/* Buttons (min height 40px; 44px on touch) */
.btn { display: inline-flex; align-items: center; height: 40px; padding: 0 18px;
  border-radius: var(--r-sm); font: 500 14px var(--font-sans); cursor: pointer; }
.btn-primary { background: var(--accent); color: var(--on-accent); border: 0; }
.btn-primary:hover { background: var(--accent-hover); text-decoration: none; }
.btn-secondary { background: transparent; color: var(--text); border: 1px solid var(--line-strong); }
.btn-secondary:hover { background: var(--bg-hover); color: var(--text-strong); text-decoration: none; }

/* Code block / terminal (with Copy button) */
.codebox { display: flex; align-items: center; justify-content: space-between; gap: 16px;
  padding: 12px 12px 12px 20px; background: var(--bg-sunken);
  border: 1px solid var(--line-strong); border-radius: var(--r-sm);
  font: 400 14px/1.6 var(--font-mono); overflow-x: auto; }
.codebox .prompt { color: var(--accent); }          /* the "$ " */
.codebox .comment { color: var(--text-dim); }       /* "# 1 pull the image" */
.codebox .btn { height: 36px; padding: 0 16px; font-size: 13px; }  /* Copy = .btn-primary */

/* Strip: N equal cells inside one bordered box, hairline dividers */
.strip { display: grid; grid-template-columns: repeat(var(--cols, 4), minmax(0, 1fr));
  border: 1px solid var(--line); border-radius: var(--r-md); overflow: hidden; }
.strip > * { padding: 20px 22px; display: flex; flex-direction: column; gap: 6px; }
.strip > * + * { border-left: 1px solid var(--line); }
.strip .num { font: 500 28px/1.1 var(--font-mono); color: var(--text-strong); }
.strip .num small { font-size: 17px; color: var(--text-dim); }
.strip .label { font-size: 13.5px; color: var(--text-muted); }

/* Step grid: same as .strip, cells padded 16px, with step number */
.step-no { font: 400 11.5px var(--font-mono); color: var(--accent); }
.step-title { font-size: 15px; font-weight: 600; color: var(--text-strong); }
.step-meta { font: 400 11.5px/1.5 var(--font-mono); color: var(--text-muted); }

/* Standalone card */
.card { padding: 18px 20px; border: 1px solid var(--line); border-radius: var(--r-sm);
  display: flex; flex-direction: column; gap: 6px; }
.card.is-highlight { border-color: var(--accent-line); }   /* at most one per section */

/* Chip (dimension names, tags) */
.chip { display: inline-block; padding: 4px 10px; border: 1px solid var(--line-strong);
  border-radius: var(--r-xs); font: 400 12px var(--font-mono); color: var(--text-nav); }

/* Role dot (Easy Kit agent roles only) */
.dot { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }

/* Progress bar (scorecard coverage) */
.bar { height: 6px; border-radius: 3px; background: var(--line-header); overflow: hidden; }
.bar > span { display: block; height: 100%; background: var(--accent); }

/* Tables (all reference tables on the three sites) */
.table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: var(--r-md); }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { text-align: left; font: 500 12px var(--font-mono); color: var(--text-muted);
  padding: 10px 16px; border-bottom: 1px solid var(--line); background: var(--bg-sunken); }
td { padding: 12px 16px; border-bottom: 1px solid var(--line); color: var(--text); vertical-align: top; }
tr:last-child td { border-bottom: 0; }
tbody tr:hover td { background: var(--bg-hover); }
```
| Component | Where it is used | | .strip (4 cols) | Easy Kit quick-reference stats; Easy Memory measured numbers | | .strip (3 cols) | Highlights / principles row on Easy Memory and Easy Verifier | | Step grid | Easy Kit pipeline (6), Easy Memory "How it works" (5), Easy Verifier scoring flow (5) | | .card | Easy Kit agent roles; Easy Memory experiments; Easy Verifier scorecard | | .codebox | Every install / run command | | .chip | Easy Verifier dimensions; Easy Kit packs and skills lists | | Tables | Hooks, packs, repo layout, memory files, update flow, dimensions, 32 areas, known limits, release notes | 
## Per-site pages
Keep each site's existing copy and section anchors. The lists below say which component renders each section; sections not listed keep their content and use plain prose plus tables.

### Easy Kit
- Header: glyph = connected nodes; name "Easy Kit"; tag supervisor kit · v2.2.0.

- Sidebar groups: // overview (Quick reference, What you get, Minimal and extended tracks) · // getting started (Install, Update flow, Settings tool, Install variants) · // the team (Agent roles, Skills, Hooks, Agent focus) · // reference (Packs, Providers, Repository layout, Memory system, MCPs, Options).

- Hero: eyebrow > multi-agent supervisor framework, h1 "Easy Kit", lede from the current hero.

- Install: label "Install" (13px/600 --text-nav), then .codebox with the real install command and a Copy button (.btn-primary).

- Quick reference: .strip 4 cols — 4 spawnable roles · 32 skills · 5/11 hooks that block · 5 optional domain packs.

- What you get → pipeline: step grid, 6 cells, numbers 00–05, each with the stage name and its outputs in .step-meta (PRD.md, BRAINSTORMING_LOG.md, codebase map, agent roster, specs, task guides, parallel worktree code, review findings, release plan). Use the real stage names from the site.

- Agent roles: 4 .cards in a row, each with a .dot in its role color and the role name in mono 13px. general-agent-template listed below as plain text (not spawnable).

- Settings tool: inputs and selects use --bg-sunken background, --line-strong border, radius --r-sm, 40px height; output in a .codebox with Copy.

- MCPs: 3 .cards (easy-verifier-mcp, easy-ui-mcp, easy-memory-mcp).

### Easy Memory
- Header: glyph = stacked note bars; name "Easy Memory"; tag memory kit · v0.1.0 prototype.

- Sidebar groups: // overview (What it is, Context, How it works) · // guide (Install, Use it, Remove it) · // reference (Measured, Known limits, Release notes, How it was built).

- Hero: eyebrow > per-repo memory for claude code, h1, lede, then buttons: "View the source on GitHub" (primary) and "Install" (secondary, anchors to #install).

- Highlights: .strip 3 cols — Local · Hooks and MCP · Measured on yourself.

- How it works: step grid 5 cells — Stop hook → Note store (~/.easy-memory/) → Word weights → Prompt hook (2,500-char frame) → MCP server (search · read · list · forget).

- Context: 3 .cards for experiments 01–03; big mono number (−58%, ~−15%, −29% / −27%); experiment 03 gets .is-highlight and the label exp 03 · shipped in --accent.

- Install: numbered steps, each with a .codebox (run tests, --dry-run, install).

- Measured: .strip 4 cols — 0.212 s prompt hook p95 · 0.066 s stop hook p95 · 0.024 s weights load · 307 tests pass.

- Known limits: table with a Status column; status shown as plain mono text (open, accepted, to run) in --text-muted — no red/green badges.

### Easy Verifier
- Header: glyph = check mark; name "Easy Verifier"; tag offline verifier · mcp + cli (replace with the version number if one exists).

- Sidebar groups: // overview (What it is, Run it) · // reference (Dimensions, 32 areas, How scoring works, Sample scorecard).

- Hero: eyebrow > offline, rule-based repository verifier, h1, lede.

- What it is: .strip 3 cols — No inferred verdicts · No guessing · Read-only and local.

- Run it: one .codebox (multi-line, no Copy button needed per line; one Copy for the block) with # comments for steps 1–3 and the real Docker and claude mcp add commands. Alternatives (Compose, stdio, CLI) as secondary links below.

- Dimensions: table (name in mono, description). change-risk row separated with a note that it is never averaged in.

- 32 areas: table; coverage state as plain mono text (core rule, optional pack, no rule yet) with no rule yet in --text-dim.

- How scoring works: step grid 5 cells — Repository → Evidence → Rules → Coverage check → Rating or abstention.

- Sample scorecard: two-column grid (280px + 1fr). Left .card: label sample scorecard · 8062b35, score 47 / 100 (mono 40px), .bar at 69% (22/32), caption "22 of 32 areas measured". Right .card: per-dimension ratings; abstentions shown as — with the word "abstained" in --text-dim.

## Rules and acceptance checklist
| Do | Don't | | Use --accent only for links, active nav, step numbers, $ prompts, primary buttons, one highlighted card per section | Fill large areas, headings or backgrounds with mint | | Separate content with 1px --line borders | Use gradients, glows, neon box-shadow, blurred backdrops | | Keep text in the defined grays | Use #000, #FFF, or saturated reds/greens for status | | Show status as plain mono words | Use colored pill badges | | Reuse the shared theme.css on all three sites | Copy tokens into each site with drift | | Keep existing copy, anchors and section order | Rewrite content or remove sections | Accessibility: every text color must pass 4.5:1 on its background (the tokens above all do on --bg); all controls are real <a>, <button>, <input> with labels; icon-only buttons get aria-label; decorative SVG gets aria-hidden="true"; touch targets at least 44px below 720px width.
Acceptance checklist for each site:
- Easy Kit restyled, all sections present

- Easy Memory restyled, all sections present

- Easy Verifier restyled, all sections present

- One shared theme.css; no hex values outside it (grep -E '#[0-9a-fA-F]{6}' finds only the token file)

- Family nav identical on all three, current site marked with mint dot and aria-current

- Only IBM Plex Sans and IBM Plex Mono load

- No gradients, glows or text shadows anywhere

- Layout checked at 1440px, 1024px, 768px and 375px; no horizontal page scroll

- Keyboard: skip link works, focus ring visible on every link and button

- Lighthouse accessibility score 95 or higher

- Easy Kit's drift test (generated page vs agents/ and skills/) still passes


