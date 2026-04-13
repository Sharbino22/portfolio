# Shri's Portfolio Website

## DEPLOYMENT RULES (READ FIRST)
- **Netlify deploys from `main` only.** Every push to `main` costs 1 build credit. Credits are limited (300/month on the free plan).
- **NEVER push directly to `main` during a work session.** Always work on a feature branch (e.g. `redesign`, `feature/dashboards`).
- **Workflow:** `git checkout -b <branch>` at the start of work. Commit freely to the branch (free, no credits). When the user says "push" or "go live", merge the branch into `main` and push once. That's 1 credit for all the accumulated work.
- **NEVER run `git push origin main` after every small change.** Batch everything into one push.
- **If already on `main`:** create a branch immediately with `git checkout -b work-session` before making any changes. Merge back at the end.
- **Ask before pushing.** Even when the user says "commit", confirm whether they also want to push to main (which triggers a deploy and costs a credit) or just commit locally.

## CURRENT STATE
- **Dark theme** with animated gradient background (#08080C base)
- **File structure:**
  - Top-level: `index.html`, `css/style.css`, `js/globe.js`, `js/main.js`
  - Project case-study pages (sibling to index): `nyrocare.html`, `survival-analysis.html`, `cv-risk-gaps.html`, `medicare-analysis.html`, `propensity-analysis.html`, `i2db-datathon.html`
  - Project source folders: `Projects/nhanes-cancer-survival/`, `Projects/cv-risk-gaps/`, `Projects/medicare-claims-analysis/`, `Projects/propensity-score-analysis/`, `Projects/I2DB_Datathon/`, `Projects/healthcare-expenditure-modeling/`, `Projects/nhanes-survival-analysis/`
  - Interactive dashboards (single-file Plotly.js + embedded JSON): `Projects/nhanes-cancer-survival/dashboard.html`, `Projects/cv-risk-gaps/dashboard.html`, `Projects/medicare-claims-analysis/dashboard.html`
- **globe.js is LOCKED** — do NOT modify unless explicitly told "edit the globe"
- Deployed on GitHub Pages via github.com/Sharbino22/portfolio

## DESIGN SYSTEM

### Theme: Dark Premium (Linear.app / Apple Pro aesthetic)
- **Background:** Dark (#08080C) with subtle animated gradient and noise texture
- **Font:** Plus Jakarta Sans ONLY (weights 400-800)
- **Primary text:** #F0EEFF (headings), #E2E0E6 (body), #9894A8 (descriptions), #6B6880 (muted)
- **Accent colors:** Indigo #818CF8, Pink #F472B6, Green #10B981, Blue #3B82F6, Amber #F59E0B
- **Cards:** Dark frosted glass — background rgba(255,255,255,0.04-0.05), border rgba(255,255,255,0.06-0.08), backdrop-filter blur
- **Nav:** Frosted glass, outlined indigo "Connect" pill button
- **No em dashes** anywhere in content
- **No AI-sounding language**

### Animations
- Spring easing: cubic-bezier(0.16,1,0.3,1) everywhere
- Scroll reveals: blur-to-sharp (filter: blur(6px) to blur(0)) + fade up
- Hero entrance: text slides from left, globe from right on page load
- Hero exit: entire hero content recedes into depth on scroll
- Cursor spotlight: soft indigo glow follows mouse
- Cursor trail: fading indigo dots on mousemove
- 3D card tilt on hover (perspective transform)
- Animated gradient borders on project cards (conic-gradient rotation)
- Text shimmer on "Research · Evidence · Strategy"
- Magnetic pull on buttons
- Floating gradient orbs in section backgrounds
- Glowing breathing lines between sections
- Ambient floating particles in Experience and Research sections

### Section Pattern
- Section label: 12px, uppercase, letter-spacing 3px, color varies per section
- Section heading: 36-42px, font-weight 800, color #F0EEFF
- Section padding: 80px top/bottom
- Scroll reveal with IntersectionObserver (threshold 0.15)

## SITE STRUCTURE

### Hero (100vh, side-by-side layout)
- LEFT: "Shri" name (no profile photo — removed for cleaner look), tagline "Physician turned healthcare strategist", "Research · Evidence · Strategy", description, tag pills, buttons (Get in touch + Request Resume), credential badges (CPH, Delta Omega, ASCO 2026, 3.94 GPA, Class Acts, Claude 101)
- RIGHT: Interactive Three.js 3D globe with 5 location markers, flight path animation, breadcrumb dots, info cards
- Globe cycles: India, St. Louis, Washington DC, Barcelona, Singapore

### My Story (id="story") — Animated Roadmap
- SVG road path that draws itself on scroll
- 4 milestone dots with dashed leader lines to text blocks
- Target bullseye with pulsing ring + target roles: Life Sciences & RWE, Healthcare Consulting, Health Tech PM, Research & Analytics

### Projects (id="projects")
- Multi-row grid mixing strategy case studies and analytical research projects
- Strategy / case studies: Nyrocare (50+ interviews, case study link), Strange Donuts Barcelona (EUR 192K), Madera Hospital ($24M)
- Analytical research projects (each with its own case-study HTML and a single-file Plotly dashboard):
  - **Oncology Survival Analysis** → `survival-analysis.html` → `Projects/nhanes-cancer-survival/dashboard.html` (KM curves, subgroup HR forest, follow-up cutoff slider; indigo theme)
  - **CV Risk in Cancer Survivors** → `cv-risk-gaps.html` → `Projects/cv-risk-gaps/dashboard.html` (BP/A1c/cholesterol control bars, trends, depression overlay; emerald theme)
  - **Medicare Rate & Utilization** → `medicare-analysis.html` → `Projects/medicare-claims-analysis/dashboard.html` (US choropleth, click-to-drilldown by state, top DRG/HCPCS bars, markup vs volume scatter; amber theme)
  - **Propensity Score Analysis** → `propensity-analysis.html` (no dashboard yet)
  - **I2DB Datathon** → `i2db-datathon.html` (no dashboard yet)
- Animated gradient borders on hover
- **Live Dashboard badge** (`.interactive-badge` in style.css) on the bottom-left of each project card image when a dashboard exists. Bold pill, color-coded per project theme via `--badge-from`/`--badge-to` CSS vars, animated pulsing dot, "LIVE DASHBOARD" label.

### Interactive Dashboards — shared conventions
All three dashboards follow the same pattern so they read as one body of work:
- **Single self-contained HTML file** with Plotly.js loaded via CDN and pre-aggregated data embedded as JSON
- Aggregation done server-side in Python (notebook or scratch script) to keep payloads small (85-320 KB)
- Dark theme matching the portfolio: bg `#0F0D2A`, text `#E0E7FF`, muted `#A5B4FC`, frosted-glass panels, Plus Jakarta Sans
- Sticky nav with "← Back to project" + "Portfolio" links
- Banner with project-themed eyebrow tag, h1, and subtitle
- Stat strip of headline numbers
- Filter row (selects + toggle groups + reset button)
- Grid of panels (full-width + 2-column)
- Footer with source/methods/attribution
- **Project-specific palettes:** Survival = indigo `#818CF8`, CV Risk = emerald `#34D399`, Medicare = amber `#F59E0B`/orange `#F97316`
- Each project's case-study HTML page has a "Now Live" eyebrow + gradient "Launch Interactive Dashboard" button under the hero subtitle, color-matched to the project theme

### Experience (id="experience") — Bridge Map
- Heading: "Research. Evidence. Strategy."
- Left: 3 pillar pills (Research & Epidemiology, Digital Health, Healthcare Strategy)
- Right: 8 role cards with colored left borders
- SVG curved connecting lines between pillars and roles

### Research (id="research") — Bento Grid
- Conference Posters (4, spans 2 rows), Publications (3), Peer Reviewerships (5)

### Education & Achievements (id="achievements")
- 3 colored degree cards (MBA, MPH, BNYS) with impact highlights
- Achievement strip: Delta Omega, Class Acts, 2x Yoga Champion, 5 Languages, Graduate Policy Scholar

### Beyond Work (id="beyond") — Bento Grid
- 7 tiles: Stargazing (photo), Creve Coeur Lake, Fitness (photo), Dogs, Fragrances, Music, Travel (photo)
- Photo tiles have dark gradient overlay for text readability

### Connect (id="contact")
- "Let's build the future of healthcare together"
- Seeking roles in life sciences, healthcare consulting, health tech, and research analytics
- Get in touch (mailto) + Request Resume (mailto with subject line)
- Email + LinkedIn (NO phone number — removed for privacy)
- "Shri 2026" footer

## NYROCARE FRAMING
- Use "Graduate Venture Project" not "Product Lead" or "Co-founder"
- Developed through WashU Skandalaris Center
- F-1 visa compliant language throughout

## TIMELINE (VERIFIED)
| Period | What |
|--------|------|
| 2016-2022 | BNYS degree (education, NOT practice) |
| June 2022 - June 2023 | Medical Officer, ANR Poly Clinic (1 year clinical practice) |
| Fall 2023 | Arrived at WashU for dual MPH/MBA |
| Oct 2023 - Oct 2024 | Strategy Consultant, Madera Hospital |
| Jan 2024 - Jan 2026 | Board Member, Community Care Center IL |
| May 2024 - Present | Graduate Venture Project, Nyrocare |
| June 2024 - Present | Cancer Epi Research Fellow, Siteman Cancer Center |
| July 2024 - Present | Healthcare Research Analyst, Stats Lab |
| Spring 2026 | TA, Public Health Seminar II |
| May 2026 | Graduation |

## GLOBE SPECS (DO NOT MODIFY)
Three.js r128, TopoJSON world-atlas, great circle arcs with slerp, pink flight path animation (#F472B6) with arrowhead (#EC4899), shortest-path rotation, 5 locations with breadcrumb dot navigation, state machine: ROTATING > ZOOMING_IN > DWELLING > ZOOMING_OUT.

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
