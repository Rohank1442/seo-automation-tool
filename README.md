# SEO Automation Agent

An autonomous, end-to-end SEO automation system designed to take a website idea from initial niche research and technical architecture scaffolding to programmatic content generation, indexing surveillance, data-driven optimization, and a continuous learning loop.

```text
User describes website idea
        ↓
v0.1 — Niche & Keyword Research
        ↓
v0.2 — Site Architecture & Website Foundation
        ↓
v0.3 — First Wave Content Generation
        ↓
v0.4 — Indexing Watch & Early Signal Detection
        ↓
v0.5 — Pivot or Double Down
        ↓
v0.6 — Full Continuous Learning Loop
```

---

## 🚀 Product Vision & Phase Roadmap

### `v0.1` — Niche & Keyword Research
You describe your idea. The agent confirms it understood you correctly and asks if you want to add anything before it starts. Then it researches:
- Topic clusters and semantic relationships
- Keywords with search volume, CPC, and difficulty metrics (DataForSEO integration / mock fallbacks)
- Long-tail variations and search queries
- People Also Ask (PAA) questions and user search intent
- Competitor content landscape, content gaps, and angle suggestions per cluster

*Everything gets saved locally as the structured data foundation for all future phases.*

---

### `v0.2` — Site & Technical Setup
The agent scaffolds a clean, fast, crawlable website foundation:
- Recommends domain structure and site hierarchy
- Generates semantic keyword grouping and cluster audits
- Sets up URL architecture and slug rules
- Maps full internal-linking graph topology (hub-and-spoke cluster links, cross-links, anchor texts)
- Generates sitemap, `robots.txt`, and technical SEO directives
- Connects Google Search Console

*The technical foundation is sorted before any content goes live.*

---

### `v0.3` — First Wave Content Generation
Using the keyword research and architecture from v0.1 and v0.2, the agent builds the first 10–20 pages across 3–4 topic clusters — deliberately targeting low-competition, long-tail keywords a new site can realistically get indexed for:
- **Normalized Page Candidates**: Merges research, audits, URLs, link topology, and technical SEO rules.
- **First-Wave Page Selection**: Multi-factor scoring prioritizing audit approval, long-tail opportunity, low competition, content gaps, and cluster diversity.
- **Structured Content Briefs**: Generates publication-ready briefs detailing H1/H2/H3 outlines, PAA questions, character-bounded metadata, target keywords, and internal links using Gemini structured JSON.
- **Publication-Ready Content Drafting**: Drafts Markdown articles adhering strictly to approved briefs and verified internal links (zero invented links).
- **Automated Content Validation**: 80-point audit verifying metadata limits, heading nesting, keyword density, intent alignment, schema, and duplicate prevention.

*Pages go live and sitemap gets submitted.*

---

### `v0.4` — Indexing Watch & Early Signal Detection
Weekly monitoring and surveillance phase:
- Checks which pages Google has indexed via Google Search Console API and URL Inspection
- Tracks pages getting early impressions vs. pages invisible after 4–6 weeks
- Flags indexation anomalies, crawl errors, and surfaces early traction signals so you know what's showing life.

---

### `v0.5` — Pivot or Double Down
Based on 6–8 weeks of empirical search performance data, the agent makes a clear call per cluster:
- **Double down** on clusters and keywords getting early traction and impressions
- **Fix / Revise** underperforming pages (adjusting titles, adding subtopics, improving intent match)
- **Prune / Drop** topics that are completely dead

*You decide, but the agent provides the data and clear recommendations.*

---

### `v0.6` — Full Continuous Learning Loop
The system shifts into compounding autonomous mode:
- Every cycle it pulls fresh GSC performance data
- Categorizes every page by performance status: `working`, `stuck`, `CTR problem`, `invisible`, or `declining`
- Mines newly discovered queries from search consoles for fresh page opportunities
- Automatically improves and refreshes existing underperforming pages
- Generates new pages based on proven patterns in your niche
- Refines its understanding of your niche and audience with each pass

*Runs on a recurring schedule indefinitely.*

---

## 📁 Repository Structure

```text
seo-automation/
├── README.md                           # Project documentation & roadmap
├── generated-pages/                    # Drop-in Next.js / React components (Copy directly to your site)
│   ├── app/                            # Next.js App Router pages (app/[slug]/page.tsx)
│   │   ├── {slug}/page.tsx
│   │   └── ...
│   └── README.md                       # Component usage instructions
├── seo-agent/
│   ├── .env.example                    # Environment variable templates
│   ├── .gitignore                      # Git ignore rules
│   ├── requirements.txt                # Python dependencies
│   └── agent/
│       ├── core/                       # LLM abstractions, DB, and config
│       │   ├── config.py               # Settings & API keys
│       │   └── llm.py                  # Gemini JSON/text LLM abstraction
│       ├── phases/                     # Pipeline execution modules
│       │   ├── v01_research.py         # v0.1 Niche & Keyword Research
│       │   ├── v02_architecture.py     # v0.2 Site Architecture & Setup
│       │   ├── v03_content_generation.py # v0.3 Content Generation & Validation
│       │   └── v03_export_frontend.py  # Interactive Next.js / React Frontend Exporter
│       ├── prompts/                    # Pydantic schemas & prompt templates
│       │   ├── v01_prompts.py          # v0.1 research schemas
│       │   ├── v02_prompts.py          # v0.2 architecture schemas
│       │   └── v03_prompts.py          # v0.3 brief, draft & audit schemas
│       └── outputs/                    # Output artifacts
│           ├── research_report.md      # v0.1 Research report
│           ├── v02/                    # v0.2 Architecture artifacts
│           │   ├── site_architecture.json
│           │   ├── keyword_groups.json
│           │   ├── keyword_group_audit.json
│           │   ├── url_architecture.json
│           │   ├── internal_linking.json
│           │   ├── technical_seo.json
│           │   └── v02_report.md
│           └── v03/                    # v0.3 Content generation artifacts
│               ├── page_candidates.json
│               ├── selected_pages.json
│               ├── content_briefs.json
│               ├── generated_content.json
│               ├── content_validation.json
│               ├── content_manifest.json
│               ├── content_generation_report.md
│               ├── v03_report.md
│               └── pages/              # Generated Markdown & JSON per page
│                   ├── {slug}.md
│                   └── {slug}.json
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.9+
- Gemini API Key (`GEMINI_API_KEY`)
- *(Optional)* DataForSEO API Credentials (`DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD`)

### 2. Install Dependencies
```bash
cd seo-agent
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file in `seo-agent/` (or set environment variables):
```env
GEMINI_API_KEY=your_gemini_api_key_here
DATAFORSEO_LOGIN=your_dataforseo_login
DATAFORSEO_PASSWORD=your_dataforseo_password
```

---

## ⚡ CLI Usage & Pipeline Commands

### Run Full v0.3 Content Generation & Validation
```bash
# Full generation with live Gemini API
python agent/phases/v03_content_generation.py

# Offline / Dry-run mode (deterministic templates & testing)
python agent/phases/v03_content_generation.py --dry-run
```

### Run Specific v0.3 Pipeline Steps
```bash
# 1. Build and save normalized page candidates only
python agent/phases/v03_content_generation.py --candidates-only

# 2. Run First-Wave page selection only (configurable range)
python agent/phases/v03_content_generation.py --select-only --min-pages 10 --max-pages 20

# 3. Generate Gemini structured content briefs only
python agent/phases/v03_content_generation.py --briefs-only

# 4. Run the 80-point automated content validation suite on existing content
python agent/phases/v03_content_generation.py --validate-only

# 5. Generate content for a single specific page slug
python agent/phases/v03_content_generation.py --slug how-to-get-free-clothes-online

# 6. Interactive Frontend Export (Prompts for Next.js App/Pages Router, TS/JS, Tailwind, Output folder)
python agent/phases/v03_export_frontend.py

# 7. Non-interactive / Automated Frontend Export to generated-pages/
python agent/phases/v03_export_frontend.py --non-interactive --framework next-app --lang ts --style tailwind
```

---

## 📊 v0.3 Artifact Inventory

| Output Artifact | Format | Description |
|---|---|---|
| `outputs/v03/page_candidates.json` | JSON | Normalized 10-candidate pool combining research, keywords, URLs, and link topology |
| `outputs/v03/selected_pages.json` | JSON | Multi-factor scored and approved First-Wave pages |
| `outputs/v03/content_briefs.json` | JSON | Gemini structured content briefs (H1/H2/H3 outlines, PAA questions, metadata, links) |
| `outputs/v03/generated_content.json` | JSON | Full generated articles, FAQs, metadata, and quality audit results |
| `outputs/v03/content_validation.json` | JSON | 80-point audit across metadata, heading hierarchy, keyword density, intent, and links |
| `outputs/v03/v03_report.md` | Markdown | Comprehensive executive summary and technical inventory report |
| `outputs/v03/pages/*.md` | Markdown | Publication-ready articles with YAML frontmatter for Next.js / CMS ingestion |
| `outputs/v03/pages/*.json` | JSON | Structured data models per generated page |

---

## 📄 License
MIT License.
