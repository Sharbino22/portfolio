# Shri's Portfolio Website — Claude Code Instructions

## THE VISION
Premium personal portfolio for Shri (Sridharan Gopalsamy Ramaswamy). The aesthetic is APPLE PRODUCT PAGE level premium — not a student project. Think apple.com/iphone or linear.app: massive whitespace, bold confident typography, content that breathes, scroll-triggered animations that feel effortless, sections that flow into each other with purpose. Every pixel intentional. Light theme but with DRAMATIC contrast and depth.

Single-page scroll with sticky nav. One separate Nyrocare case study page later.

## WHAT MAKES THIS NOT LOOK LIKE A STUDENT SITE
- MASSIVE whitespace between sections (150-200px padding)
- Typography does the heavy lifting — huge section headings (48-64px), generous line height
- Content cards float with subtle shadows and depth, not flat boxes
- Scroll animations are smooth and SLOW — elements glide in, not pop in
- Background has subtle depth: soft gradients that shift, maybe a very faint grain texture
- No clutter. Every element earns its space.
- Interactions feel premium: smooth hovers, spring-eased transitions, nothing snaps

## CURRENT STATE
- `portfolio.html` has the hero section with working Three.js 3D globe
- Hero: text LEFT, globe RIGHT, side by side, 100vh
- DO NOT modify the Three.js globe code unless specifically asked
- The location info cards that appear below the globe during rotation feel too large/clunky — make them more compact and refined

## CRITICAL DESIGN RULES
- **Font:** Plus Jakarta Sans ONLY (weights 400-800)
- **No em dashes** anywhere in content
- **No AI-sounding language** — write like a thoughtful human
- **Primary colors:** Indigo (#1E1B4B, #312E81, #4338CA, #6366F1)
- **Accent colors:** Green #10B981, Pink #F472B6, Blue #3B82F6, Amber #F59E0B
- **Background:** Soft animated gradient, subtly shifting between very light colors. NOT flat white. Think Apple's slight color washes behind content sections. Each section can have a slightly different tint to create visual rhythm.
- **Cards:** Frosted glass — background: rgba(255,255,255,0.85), backdrop-filter: blur(24px), border: 1px solid rgba(99,102,241,0.06), border-radius: 20px, box-shadow with multiple layers for depth
- **Animations:** Spring easing cubic-bezier(0.16,1,0.3,1). Scroll-triggered using IntersectionObserver. Elements should fade up SLOWLY (0.8-1s duration) with staggered delays. Think Apple keynote slide transitions.
- **Section titles:** Small uppercase label (12px, letter-spacing 0.15em, color #818CF8) + large bold heading below (48px desktop, 32px mobile). Centered.
- **Section spacing:** 150px padding-top/bottom on desktop, 100px mobile
- **Nav:** Sticky, position:fixed, frosted glass, subtle shadow on scroll
- **Keep single-file approach** for portfolio.html

## CORRECTED TIMELINE (VERIFIED FROM RESUME)

| Period | What |
|--------|------|
| 2016-2022 | BNYS degree at SDM College, Rajiv Gandhi University (education, NOT practice) |
| Oct 2021 - Oct 2022 | Junior Doctor, SDM Institute (overlaps with final year of degree) |
| June 2022 - June 2023 | Medical Officer, ANR Poly Clinic, Karnataka India (1 year of clinical practice) |
| Fall 2023 | Arrived at WashU for dual MPH/MBA |
| Oct 2023 - Oct 2024 | Strategic Planning Consultant, Madera Hospital (capstone) |
| Jan 2024 - Jan 2026 | Board Member, Community Care Center IL |
| May 2024 - Present | Product Lead, Nyrocare |
| June 2024 - Present | Cancer Epi Research Fellow, Siteman Cancer Center |
| July 2024 - Present | Healthcare Research Analyst, Stats Lab |
| Spring 2026 | TA, Public Health Seminar II |
| May 2026 | Graduation |

IMPORTANT: Shri practiced medicine for approximately 1 year (2022-2023), not 5-6 years. The BNYS degree was 6 years of education. Do not conflate education with practice duration.

## SITE STRUCTURE

### Section 1: HERO (exists, needs refinements)
- Side-by-side: text left, globe right, 100vh
- Globe 380px default, 320px mobile, 420px large
- Location info cards: make them MORE COMPACT — smaller text, tighter padding, refined. Currently they feel too large.
- Click markers to explore + auto-rotate cycle
- Sticky nav with smooth scroll to anchors

### Section 2: MY STORY (id="story")
**Format: Timeline nodes with text always visible. No click-to-expand.**

Three nodes connected by a subtle vertical line. Each node has a colored dot, year label, title, and 2-3 sentence paragraph visible at all times. They animate in on scroll (staggered, slow fade-up).

Node 1 — dot color: Pink (#F472B6)
Year: "2022-2023"
Title: "The Physician"
Text: "After completing my degree in integrative medicine, I practiced as a Medical Officer in Karnataka, India. I treated patients across primary care and community health, redesigned clinic EHR workflows, and built public health outreach programs. I could help the person in front of me, but I couldn't fix the system failing them."

Node 2 — dot color: Amber (#F59E0B)
Year: "2023"
Title: "The Realization"
Text: "Healthcare's biggest problems aren't clinical. Research exists but doesn't reach patients. Technology gets built without understanding workflows. Strategy gets made without clinical context. I realized someone needs to carry all three, not just collaborate across silos."

Node 3 — dot color: Indigo (#6366F1)
Year: "2024-2026"
Title: "The Bridge Builder"
Text: "That's why I'm at Washington University doing both an MPH and an MBA. Epidemiology and biostatistics for the research. Strategy and product thinking for the business side. Together, they let me build where research, technology, and implementation actually meet."

Section label: "MY STORY"
Section heading: "How I got here"

### Section 3: WHAT I'VE BUILT (id="projects")
1+2 card grid. Apple-style: lots of space, cards with generous padding.

Top (full width, hero-sized card):
- **Nyrocare** — Voice AI health companion for chronic disease management. React Native, Node.js, RAG architecture, Claude API. 50+ stakeholder interviews. Product Lead through WashU Skandalaris Center. "View case study" link. Tags: Product Strategy, Health Tech, AI/ML, User Research.

Bottom row (two equal cards):
- **Strange Donuts Barcelona** — MBA Global Immersion group project. Market entry strategy for US food business expanding to Spain. EUR 192K investment model, 29-month payback. Tags: Market Entry, Financial Modeling, Consumer Research.
- **Madera Community Hospital** — Healthcare strategy capstone. Turnaround strategy reducing losses from $27M to $3M. SWOT, Triple Aim, Lean 5S. Tags: Healthcare Strategy, Operations, Turnaround.

Section label: "WHAT I'VE BUILT"
Section heading: "Projects"

### Section 4: RESEARCH & PUBLICATIONS (id="research")
Animated counter at top: "6+ publications across 4 conferences" (numbers count up on scroll)

Two columns on desktop, stacked on mobile:

LEFT — First Author:
- ASCO 2026: "Lipid-Lowering Therapy Use Among Cancer Survivors Undergoing Lung Cancer Screening"
- AAIC Neuroscience Next 2026: "Hypertension and Cognitive Difficulty in Missouri's Elderly Population"
- WashU GRS: Cervical cancer screening disparities — badge: "3rd Place"
- Siteman Cancer Research Symposium: LLT/statin study

RIGHT — Co-Author + Peer Review:
- JAD 2025: Anti-seizure medications and Alzheimer's risk scoping review
- Multiple manuscripts in preparation
- Peer reviewer pills: PLOS ONE, APHA, JHEOR, Springer Nature, Frontiers in Public Health

Section label: "RESEARCH"
Section heading: "Publications & Peer Review"

### Section 5: EXPERIENCE (id="experience")
Vertical timeline with subtle line on left. Each role = a node.

Current roles: pulsing green dot
Past roles: solid muted dot

Color by category: Purple=Research, Green=Building, Blue=Strategy, Pink=Clinical

Roles (chronological, newest first):
- TA, Public Health Seminar II (Spring 2026) — 54 students, 3 sections [Blue]
- Product Lead, Nyrocare (May 2024-Present) — Voice AI health companion. React Native, RAG, Claude API. [Green]
- Cancer Epi Research Fellow, Siteman (June 2024-Present) — BRFSS/NHANES analysis. First-author publications. [Purple]
- Healthcare Research Analyst, Stats Lab (July 2024-Present) — Team 3 to 8. 2.5x engagement. R, Python, Tableau. [Purple]
- Board Member, Community Care Center IL (Jan 2024-Jan 2026) — Grant database, cost reduction. [Blue]
- Strategic Planning Consultant, Madera Hospital (Oct 2023-Oct 2024) — $27M to $3M turnaround. [Blue]
- Medical Officer, ANR Poly Clinic India (June 2022-June 2023) — 5,000+ patients, EHR redesign. [Pink]

Section label: "EXPERIENCE"
Section heading: "Where I've worked"

### Section 6: ACHIEVEMENTS & EDUCATION (id="achievements")
Three degree cards in a row (stack on mobile):
- MBA (STEM) — WashU Olin Business School, May 2026
- MPH (Epi & Biostatistics) — WashU Brown School, GPA 3.94, May 2026
- BNYS — SDM College, Rajiv Gandhi University, Graduated with honors, 2022

Badge grid below:
Graduate Policy Scholar, Class Acts Feature (~170K circulation), CPH Certified, Delta Omega (nominated), State Yoga Champion x2, National Representative, 5 Languages (Tamil, Telugu, Kannada, Malayalam, English), Global Immersions (Barcelona, Singapore, DC)

Section label: "ACHIEVEMENTS"
Section heading: "Education & Honors"

### Section 7: BEYOND WORK (id="beyond")
2x3 card grid. Each card: emoji, title, one-line text. Warm and personal.
- Stargazing — St. Louis Astronomical Society, Stacy Park
- Creve Coeur Lake — favorite spot, long conversations
- Fitness — bodybuilding
- Dogs — loves them
- Fragrances — Lattafa Asad
- Tamil Cinema — comfort zone

Section label: "BEYOND WORK"
Section heading: "When I'm not working"

### Section 8: CONNECT (id="contact")
Centered. "Let's connect" heading. "Currently in St. Louis. Open to relocating."
Email: g.sridharan@wustl.edu | LinkedIn: linkedin.com/in/dr-sri-dharan-shri | Phone: 314-203-3417
Resume download button. Copyright: 2026 Sridharan Gopalsamy Ramaswamy

## GLOBE SPECS (DO NOT MODIFY)
Three.js r128, TopoJSON world-atlas, royal blue ocean, pearl white continents, Fresnel atmosphere shader, 5 location markers with click interaction, state machine animation, rotation/tilt formulas locked.

## DESIGN PATTERNS
- `.reveal` + IntersectionObserver for scroll (threshold: 0.15, rootMargin: "0px 0px -50px 0px")
- Frosted glass cards (specs above)
- Pill tags with colored borders
- Primary/secondary buttons with hover lift
- Spring easing everywhere: cubic-bezier(0.16,1,0.3,1)
- Animation duration: 0.8-1.0s (slow and premium, not snappy)
- Stagger delays: 0.1-0.15s between sibling elements
