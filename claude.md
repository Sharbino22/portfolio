# Shri's Portfolio Website

## CURRENT STATE
- **Dark theme** with animated gradient background (#08080C base)
- **File structure:** index.html, css/style.css, js/globe.js, nyrocare.html
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
- LEFT: Profile photo + "Shri" name, tagline "Physician turned healthcare strategist", "Research · Evidence · Strategy", description, tag pills, buttons (Get in touch + Request Resume), credential badges (CPH, Delta Omega, ASCO 2026, 3.94 GPA, Class Acts, Claude 101)
- RIGHT: Interactive Three.js 3D globe with 5 location markers, flight path animation, breadcrumb dots, info cards
- Globe cycles: India, St. Louis, Washington DC, Barcelona, Singapore

### My Story (id="story") — Animated Roadmap
- SVG road path that draws itself on scroll
- 4 milestone dots with dashed leader lines to text blocks
- Target bullseye with pulsing ring + target roles: Life Sciences & RWE, Healthcare Consulting, Health Tech PM, Research & Analytics

### Projects (id="projects")
- 3-column grid with impact metrics
- Nyrocare (50+ interviews, case study link), Strange Donuts Barcelona (EUR 192K), Madera Hospital ($24M)
- Animated gradient borders on hover

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
