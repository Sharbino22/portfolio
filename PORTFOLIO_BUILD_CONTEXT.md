# Shri's Portfolio Website — Build Context Document
**Last updated:** March 21, 2026
**Status:** Hero section complete, remaining sections to build

---

## WHAT EXISTS (portfolio.html)

A production-ready hero section saved as `portfolio.html`. Single HTML file with embedded CSS and JS. Opens directly in any browser.

### Tech Stack
- **HTML/CSS/JS** — single file, no framework
- **Three.js r128** (loaded via CDN) — 3D globe rendering
- **TopoJSON / world-atlas** (loaded via CDN) — real geographic coastline data
- **Plus Jakarta Sans** (Google Fonts) — typography
- **Deployment target:** GitHub Pages or Netlify (free, no platform branding)

### Hero Section Structure (top to bottom)
1. **Nav bar** — frosted glass, logo "S.Ramaswamy", links: My Story, Projects, Research, Beyond Work, Connect button
2. **Badge** — green pulse dot + "Available May 2026"
3. **"Shri"** — 84-100px bold gradient text
4. **"Sridharan Gopalsamy Ramaswamy"** — small gray subtitle
5. **"Integrative physician"** — dark headline
6. **"Research · Technology · Strategy"** — indigo gradient headline
7. **Description** — "Dual MPH/MBA at Washington University in St. Louis. I work across healthcare research, epidemiology, health tech, and strategy — building solutions where these disciplines meet, not where they stay apart."
8. **"MY JOURNEY" label** — uppercase, bold, indigo
9. **3D Globe** — 540px (desktop), Three.js with real geography
10. **Location info card** — appears below globe during rotation
11. **Tags row** — Epidemiology & Biostatistics, Product Lead Nyrocare, Healthcare Strategy, Healthcare Researcher
12. **Buttons** — "Get in touch" (primary) + "Resume" (secondary)
13. **Stats bar** — 6+ Publications | 3 Global projects | 800+ Community mentored
14. **Scroll hint** — "Scroll to explore" + animated arrow

### Globe Specifications (LOCKED)
- **Ocean:** Royal blue gradient (#1a3a6e → #2d60a8)
- **Continents:** Pearl white/cream (#ece8e2) — real TopoJSON coastline data
- **Atmosphere:** Fresnel shader glow (blue, additive blending)
- **Markers:** 5 locations with colored dots, white centers, pulsing rings
- **Arcs:** Connection lines between locations
- **Animation:** State machine with 4 phases: ROTATING → ZOOMING_IN → DWELLING (10 sec) → ZOOMING_OUT → next location
- **Rotation formula:** `getTargetRotY(lng) = -(lng+90) * PI/180`
- **Tilt formula:** `getTargetRotX(lat) = lat * PI/180 * 0.35`
- **Speed:** Rotation 0.008, zoom 0.01 (deliberately slow for readability)
- **Click globe** to manually skip to next location

### Globe Locations (in order)
| # | Name | Lat | Lng | Color | Tag | Project |
|---|------|-----|-----|-------|-----|---------|
| 0 | Karnataka, India | 15.3 | 75.1 | Purple #8B5CF6 | WHERE IT STARTED | Medical Officer · Integrative Physician |
| 1 | St. Louis, USA | 38.63 | -90.20 | Indigo #6366F1 | HOME BASE | Dual MPH/MBA · Researcher · Product Builder |
| 2 | Barcelona, Spain | 41.39 | 2.17 | Pink #F472B6 | GLOBAL IMMERSION | Market Entry Strategy |
| 3 | Singapore | 1.35 | 103.82 | Green #10B981 | GLOBAL IMMERSION | Global Operations Strategy |
| 4 | Washington DC, USA | 38.91 | -77.04 | Blue #3B82F6 | GLOBAL IMMERSION | Policy & Institutions |

### Design System (LOCKED)
- **Font:** Plus Jakarta Sans (weights: 400, 500, 600, 700, 800)
- **Background:** Multi-layer: radial gradient mesh + dot grid + noise texture + floating accent blobs
- **Primary colors:** Indigo (#1E1B4B, #312E81, #4338CA, #6366F1)
- **Accent colors:** Green #10B981, Pink #F472B6, Blue #3B82F6, Amber for Healthcare Researcher tag
- **Cards:** Frosted glass (rgba white 0.92 + backdrop-filter blur 24px)
- **Buttons:** Primary = indigo gradient + shadow, Secondary = frosted glass + border
- **Tags:** Pill-shaped, white bg, colored border + text
- **Stats:** Glassmorphism card with dividers
- **Animations:** Spring easing cubic-bezier(0.16,1,0.3,1), staggered entrance delays

### Known Issues / Polish Items
- Globe rotation accuracy: India and Singapore are accurate. Barcelona, DC, St. Louis improved with 0.35 tilt multiplier but may need further tuning. The longitude rotation is correct; the issue is that high-latitude locations (38-41°N) need strong X-tilt to center visually.
- The globe currently does NOT have traveling pulse/comet animations along arcs (removed during debugging). Could be re-added.
- Mobile testing needed — globe renders but performance on low-end phones unknown.

---

## WHAT'S REMAINING (8-section site)

### Section 2: MY STORY
**Content (LOCKED):**
Physician → saw individual patient care couldn't fix systemic problems → wanted to work at population AND system level → that's why MPH + MBA. Core belief: the gap between research, technology, and implementation can't be fixed by collaboration alone — one person needs to carry all three.

### Section 3: WHAT I'VE BUILT (Projects)
- **Nyrocare** — full case study spotlight (React Native, Node.js, RAG, Claude API, 50+ user interviews)
- **Strange Donuts Barcelona** — market entry strategy (group project, financial modeling)
- **Madera Hospital** — $27M→$3M turnaround strategy

### Section 4: RESEARCH & PUBLICATIONS
- First-author / co-author split
- JAD 2025, AAIC 2026, ASCO 2026, WashU GRS (3rd place), Siteman symposium
- Peer reviewer badges: PLOS ONE, APHA, JHEOR, Springer Nature, Frontiers
- In-prep manuscripts

### Section 5: EXPERIENCE
- Compact timeline format
- Key roles: Nyrocare, Stats Lab, Siteman, TA, Community Care Center Board, Madera, GRID Lab, Medical Officer

### Section 6: ACHIEVEMENTS & EDUCATION
- Three degrees (MBA, MPH, BNYS)
- Honors: Graduate Policy Scholar, Class Acts feature, CPH, Delta Omega nomination, 4 SPH award nominations
- State Level Yoga Champion (twice), National Representative
- 5 languages

### Section 7: BEYOND WORK
- Stargazing (St. Louis Astronomical Society)
- Creve Coeur Lake
- Fitness / bodybuilding
- Dogs, fragrances, Tamil cinema, travel

### Section 8: CONNECT
- Email: g.sridharan@wustl.edu
- LinkedIn: linkedin.com/in/dr-sri-dharan-shri
- Phone: 314-203-3417
- Resume download

---

## DESIGN PREFERENCES (for future Claude sessions)

- **No em dashes** in professional content
- **No AI-sounding language** — natural, direct
- **Plus Jakarta Sans** is the locked typeface
- **Light/white theme** — no dark sections
- **Spring easing** for all animations
- **Globe is the centerpiece** of the hero — it's the first thing people notice
- Shri prefers **iterative visual previews** — show him something, get feedback, refine
- He types fast with typos — interpret intent
- Prefers **Claude to make judgment calls** rather than asking questions
- **Copy-paste ready outputs** without over-explanation
- When building sections: **build one at a time**, get approval, move to next

---

## RECOMMENDED WORKFLOW

### Option A: Continue in Claude.ai (current approach)
- Good for design decisions, content writing, previewing widgets
- Limited by chat length
- Output: HTML files downloaded and opened locally

### Option B: Claude Code (RECOMMENDED for build phase)
- Install Claude Code CLI
- Create a GitHub repo for the portfolio
- Claude Code can read/write files directly, run dev servers, commit code
- Much better for iterating on a real codebase
- Can split into multiple files (HTML, CSS, JS) for maintainability
- Can set up GitHub Pages deployment directly

### Suggested next steps:
1. Download portfolio.html from this chat
2. Create a GitHub repo (e.g., `shri-portfolio`)
3. Push portfolio.html as index.html
4. Enable GitHub Pages (Settings → Pages → Deploy from branch)
5. Use Claude Code for remaining sections
6. Share this context doc with Claude Code so it has full context

---

## FILE REFERENCE
- `portfolio.html` — Current hero section (production-ready)
- This document — Full context for any future Claude session
