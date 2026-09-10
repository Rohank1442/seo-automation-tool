"""
v0.3 — Interactive Frontend Component Exporter.

This module reads generated page data directly from `outputs/v03/pages/*.json`
and `outputs/v03/pages/*.md`, prompts the user interactively (or accepts CLI flags),
and compiles drop-in Next.js / React components into a clean, dedicated top-level
`generated-pages/` folder.

Features:
- Framework targets: Next.js App Router (`app/{slug}/page.tsx`), Next.js Pages Router (`pages/{slug}.tsx`), React.js SPA
- Language options: TypeScript (`.tsx`) or JavaScript (`.jsx`)
- Styling options: Tailwind CSS (with @tailwindcss/typography prose) or Semantic HTML + CSS
- Embeds verified Next.js `<Link>` internal links, metadata objects, and JSON-LD Schema markup
- Interactive CLI prompt with smart defaults + non-interactive CLI arguments for automation
"""

import argparse
import html
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("v03_export_frontend")


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure console logging."""
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [Frontend-Export] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# ============================================================
# PATH CONSTANTS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = AGENT_DIR.parent.parent if (AGENT_DIR.parent / "agent").exists() else AGENT_DIR.parent
OUTPUTS_V03_PAGES_DIR = AGENT_DIR / "outputs" / "v03" / "pages"
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "generated-pages"


# ============================================================
# CONFIGURATION MODEL
# ============================================================

@dataclass
class ExportConfig:
    framework: str = "next-app"    # "next-app", "next-pages", "react-spa"
    language: str = "ts"           # "ts", "js"
    styling: str = "tailwind"      # "tailwind", "semantic"
    output_dir: Path = DEFAULT_EXPORT_DIR
    include_dynamic_template: bool = True
    non_interactive: bool = False


# ============================================================
# STEP 1: LOAD INDIVIDUAL PAGES FROM `outputs/v03/pages/`
# ============================================================

def load_pages_from_directory(pages_dir: Path) -> List[Dict[str, Any]]:
    """
    Directly scans and loads individual page models and markdown files from `outputs/v03/pages/`.
    Returns list of combined page dictionaries.
    """
    if not pages_dir.exists():
        raise FileNotFoundError(f"Pages directory not found: {pages_dir}. Please run content generation first.")

    json_files = sorted(pages_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No .json files found in {pages_dir}.")

    pages: List[Dict[str, Any]] = []

    for json_path in json_files:
        slug = json_path.stem
        md_path = pages_dir / f"{slug}.md"

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                page_data = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load JSON file {json_path}: {e}")
            continue

        md_content = ""
        if md_path.exists():
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
            except Exception as e:
                logger.warning(f"Could not read markdown file {md_path}: {e}")

        # Ensure markdown_content is populated
        if not page_data.get("markdown_content") and md_content:
            page_data["markdown_content"] = md_content

        pages.append(page_data)

    logger.info(f"Loaded {len(pages)} pages directly from: {pages_dir}")
    return pages


# ============================================================
# STEP 2: MARKDOWN TO CLEAN JSX / REACT CONVERTER
# ============================================================

def escape_jsx_text(text: str) -> str:
    """Safely escape special characters in JSX text nodes."""
    return text.replace("{", "&#123;").replace("}", "&#125;")


def convert_inline_markdown_to_jsx(text: str, framework: str = "next-app", styling: str = "tailwind") -> str:
    """
    Convert inline markdown elements (bold, italic, links, inline code) into valid JSX.
    Converts [Anchor](url) to Next.js <Link> or standard <a>.
    """
    link_class = 'className="text-blue-600 hover:text-blue-800 underline dark:text-blue-400 dark:hover:text-blue-300"' if styling == "tailwind" else 'className="article-link"'

    def replace_link(match):
        anchor_text = escape_jsx_text(match.group(1))
        url = match.group(2)
        if framework in ["next-app", "next-pages"]:
            return f'<Link href="{url}" {link_class}>{anchor_text}</Link>'
        elif framework == "react-spa":
            return f'<Link to="{url}" {link_class}>{anchor_text}</Link>'
        return f'<a href="{url}" {link_class}>{anchor_text}</a>'

    # Convert markdown links
    result = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)

    # Convert bold **text**
    result = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', result)

    # Convert italic *text*
    result = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', result)

    # Convert inline code `code`
    code_class = 'className="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-sm font-mono text-pink-600 dark:text-pink-400"' if styling == "tailwind" else 'className="inline-code"'
    result = re.sub(r'`([^`]+)`', rf'<code {code_class}>\1</code>', result)

    return result


def convert_markdown_body_to_jsx(markdown_text: str, framework: str = "next-app", styling: str = "tailwind") -> str:
    """
    Transform Markdown content into clean, semantic React JSX markup.
    Omits YAML frontmatter, ignores outer H1 (handled in header),
    and transforms H2, H3, paragraphs, lists, and callouts into clean JSX.
    """
    clean_md = re.sub(r"^---[\s\S]*?---\n*", "", markdown_text, flags=re.MULTILINE).strip()

    lines = clean_md.splitlines()
    jsx_nodes: List[str] = []
    current_list: List[str] = []

    h2_class = 'className="text-2xl font-bold text-gray-900 dark:text-white mt-10 mb-4 pb-2 border-b border-gray-200 dark:border-gray-800"' if styling == "tailwind" else 'className="section-title"'
    h3_class = 'className="text-xl font-semibold text-gray-800 dark:text-gray-100 mt-6 mb-3"' if styling == "tailwind" else 'className="subsection-title"'
    p_class = 'className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4"' if styling == "tailwind" else 'className="paragraph"'
    ul_class = 'className="space-y-2 list-disc list-inside text-gray-700 dark:text-gray-300 mb-6 pl-2"' if styling == "tailwind" else 'className="bullet-list"'

    def flush_list():
        nonlocal current_list
        if current_list:
            items_jsx = "\n".join(f"              <li>{item}</li>" for item in current_list)
            jsx_nodes.append(f"            <ul {ul_class}>\n{items_jsx}\n            </ul>")
            current_list = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            flush_list()
            continue

        # Skip H1 heading as it is rendered cleanly in the <header> block
        if stripped.startswith("# ") and not stripped.startswith("## "):
            flush_list()
            continue

        # If it reaches the FAQ heading in markdown, stop body parsing (rendered via custom accordion)
        if "frequently asked questions" in stripped.lower() and stripped.startswith("##"):
            flush_list()
            break

        # H2 Headings
        if stripped.startswith("## "):
            flush_list()
            h2_text = stripped[3:].strip()
            jsx_h2 = convert_inline_markdown_to_jsx(h2_text, framework, styling)
            jsx_nodes.append(f'            <h2 {h2_class}>{jsx_h2}</h2>')
            continue

        # H3 Headings
        if stripped.startswith("### "):
            flush_list()
            h3_text = stripped[4:].strip()
            jsx_h3 = convert_inline_markdown_to_jsx(h3_text, framework, styling)
            jsx_nodes.append(f'            <h3 {h3_class}>{jsx_h3}</h3>')
            continue

        # Bullet List Items
        if stripped.startswith("- ") or stripped.startswith("* "):
            item_text = stripped[2:].strip()
            jsx_item = convert_inline_markdown_to_jsx(item_text, framework, styling)
            current_list.append(jsx_item)
            continue

        # Regular Paragraph
        flush_list()
        jsx_p = convert_inline_markdown_to_jsx(stripped, framework, styling)
        jsx_nodes.append(f'            <p {p_class}>{jsx_p}</p>')

    flush_list()
    return "\n".join(jsx_nodes)


# ============================================================
# STEP 3: NEXT.JS COMPONENT BUILDERS
# ============================================================

def to_pascal_case(slug: str) -> str:
    """Convert slug or title to valid PascalCase React component name."""
    clean = re.sub(r'[^a-zA-Z0-9]', ' ', slug)
    words = clean.split()
    return "".join(w.capitalize() for w in words) + "Page"


def generate_faq_accordion_jsx(faq_items: List[Dict[str, Any]], styling: str = "tailwind") -> str:
    """Generate accessible JSX FAQ Accordion block."""
    if not faq_items:
        return ""

    details_class = 'className="group bg-gray-50 dark:bg-gray-900/60 p-5 rounded-xl border border-gray-200 dark:border-gray-800 transition-all duration-200"' if styling == "tailwind" else 'className="faq-item"'
    summary_class = 'className="flex justify-between items-center font-semibold text-lg text-gray-900 dark:text-gray-100 cursor-pointer list-none"' if styling == "tailwind" else 'className="faq-question"'
    ans_class = 'className="mt-3 text-gray-600 dark:text-gray-300 leading-relaxed text-base"' if styling == "tailwind" else 'className="faq-answer"'

    faq_blocks = []
    for item in faq_items:
        q = html.escape(item.get("question", ""))
        a = html.escape(item.get("answer", ""))
        arrow = '<span className="ml-4 text-blue-600 transition-transform group-open:rotate-180">↓</span>' if styling == "tailwind" else '<span>↓</span>'
        faq_blocks.append(f"""            <details {details_class}>
              <summary {summary_class}>
                <span>{q}</span>
                {arrow}
              </summary>
              <p {ans_class}>{a}</p>
            </details>""")

    h2_class = 'className="text-2xl font-bold text-gray-900 dark:text-white mb-6"' if styling == "tailwind" else 'className="faq-title"'
    section_class = 'className="mt-14 pt-8 border-t border-gray-200 dark:border-gray-800"' if styling == "tailwind" else 'className="faq-section"'

    items_joined = "\n".join(faq_blocks)
    return f"""          <section {section_class}>
            <h2 {h2_class}>Frequently Asked Questions</h2>
            <div className="space-y-4">
{items_joined}
            </div>
          </section>"""


def build_nextjs_app_router_page(
    page: Dict[str, Any],
    config: ExportConfig,
) -> str:
    """
    Generate a complete, production-ready Next.js App Router component (`app/{slug}/page.tsx`).
    Includes typed Metadata export, JSON-LD Schema, and clean JSX content.
    """
    slug = page.get("slug", "untitled")
    component_name = to_pascal_case(slug)
    meta = page.get("metadata", {})
    brief = page.get("brief", {})

    title = brief.get("meta_title") or meta.get("seo_title") or page.get("title", "")
    h1 = brief.get("h1") or page.get("h1") or page.get("title", "")
    description = brief.get("meta_description") or meta.get("meta_description", "")
    canonical = page.get("canonical_url") or meta.get("canonical_url", f"https://example.com/{slug}/")
    robots = meta.get("robots", "index, follow")
    schema_type = page.get("schema_type") or meta.get("schema_type", "Article")
    cluster = page.get("cluster", "Topic")
    page_type = page.get("page_type", "guide").capitalize()
    faq_items = page.get("faq", {}).get("faq_items", []) or page.get("faq_items", [])

    body_jsx = convert_markdown_body_to_jsx(page.get("markdown_content", ""), framework="next-app", styling=config.styling)
    faq_jsx = generate_faq_accordion_jsx(faq_items, styling=config.styling)

    # Build Schema.org JSON-LD object
    json_ld_schema = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "headline": h1,
        "description": description,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical,
        },
    }

    if faq_items:
        json_ld_schema["mainEntity"] = [
            {
                "@type": "Question",
                "name": item.get("question"),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item.get("answer"),
                },
            }
            for item in faq_items
        ]

    json_ld_str = json.dumps(json_ld_schema, indent=2)

    imports_block = """import type { Metadata } from 'next';
import Link from 'next/link';""" if config.language == "ts" else """import Link from 'next/link';"""

    type_annotation = ": Metadata" if config.language == "ts" else ""
    safe_title = title.replace('"', '\\"')
    safe_desc = description.replace('"', '\\"')
    safe_h1 = h1.replace('"', '&quot;')
    safe_canonical = canonical.replace('"', '\\"')

    metadata_block = f"""// SEO Metadata for Next.js App Router
export const metadata{type_annotation} = {{
  title: "{safe_title}",
  description: "{safe_desc}",
  alternates: {{
    canonical: "{safe_canonical}",
  }},
  robots: "{robots}",
  openGraph: {{
    title: "{safe_title}",
    description: "{safe_desc}",
    url: "{safe_canonical}",
    type: "article",
  }},
}};"""

    container_class = 'className="min-h-screen bg-white dark:bg-gray-950 py-12 px-4 sm:px-6 lg:px-8"' if config.styling == "tailwind" else 'className="article-container"'
    article_class = 'className="max-w-4xl mx-auto"' if config.styling == "tailwind" else 'className="article-wrapper"'
    header_class = 'className="mb-10 text-left"' if config.styling == "tailwind" else 'className="article-header"'
    badge_class = 'className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 uppercase tracking-wider mb-3"' if config.styling == "tailwind" else 'className="badge"'
    h1_class = 'className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-gray-900 dark:text-white tracking-tight leading-tight"' if config.styling == "tailwind" else 'className="main-heading"'

    return f"""{imports_block}

{metadata_block}

export default function {component_name}() {{
  // Schema.org JSON-LD Structured Data
  const jsonLd = {json_ld_str};

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{{{ __html: JSON.stringify(jsonLd) }}}}
      />
      <main {container_class}>
        <article {article_class}>
          <header {header_class}>
            <div {badge_class}>
              {cluster} • {page_type}
            </div>
            <h1 {h1_class}>
              {safe_h1}
            </h1>
          </header>

          <div className="prose prose-lg dark:prose-invert max-w-none">
{body_jsx}
          </div>

{faq_jsx}
        </article>
      </main>
    </>
  );
}}
"""


def build_nextjs_pages_router_page(
    page: Dict[str, Any],
    config: ExportConfig,
) -> str:
    """Generate Next.js Pages Router component (`pages/{slug}.tsx`)."""
    slug = page.get("slug", "untitled")
    component_name = to_pascal_case(slug)
    meta = page.get("metadata", {})
    brief = page.get("brief", {})

    title = brief.get("meta_title") or meta.get("seo_title") or page.get("title", "")
    h1 = brief.get("h1") or page.get("h1") or page.get("title", "")
    description = brief.get("meta_description") or meta.get("meta_description", "")
    canonical = page.get("canonical_url") or meta.get("canonical_url", f"https://example.com/{slug}/")
    cluster = page.get("cluster", "Topic")
    page_type = page.get("page_type", "guide").capitalize()
    faq_items = page.get("faq", {}).get("faq_items", []) or page.get("faq_items", [])

    body_jsx = convert_markdown_body_to_jsx(page.get("markdown_content", ""), framework="next-pages", styling=config.styling)
    faq_jsx = generate_faq_accordion_jsx(faq_items, styling=config.styling)

    safe_title = title.replace('"', '\\"')
    safe_desc = description.replace('"', '\\"')
    safe_h1 = h1.replace('"', '&quot;')
    safe_canonical = canonical.replace('"', '\\"')

    return f"""import Head from 'next/head';
import Link from 'next/link';

export default function {component_name}() {{
  return (
    <>
      <Head>
        <title>{safe_title}</title>
        <meta name="description" content="{safe_desc}" />
        <link rel="canonical" href="{safe_canonical}" />
      </Head>
      <main className="min-h-screen bg-white dark:bg-gray-950 py-12 px-4 sm:px-6 lg:px-8">
        <article className="max-w-4xl mx-auto">
          <header className="mb-10">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 uppercase tracking-wider mb-3">
              {cluster} • {page_type}
            </span>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-gray-900 dark:text-white tracking-tight">
              {safe_h1}
            </h1>
          </header>

          <div className="prose prose-lg dark:prose-invert max-w-none">
{body_jsx}
          </div>

{faq_jsx}
        </article>
      </main>
    </>
  );
}}
"""


def build_react_spa_page(
    page: Dict[str, Any],
    config: ExportConfig,
) -> str:
    """Generate pure React SPA component."""
    slug = page.get("slug", "untitled")
    component_name = to_pascal_case(slug)
    h1 = page.get("title", "")
    cluster = page.get("cluster", "Topic")
    page_type = page.get("page_type", "guide").capitalize()
    faq_items = page.get("faq", {}).get("faq_items", []) or page.get("faq_items", [])

    body_jsx = convert_markdown_body_to_jsx(page.get("markdown_content", ""), framework="react-spa", styling=config.styling)
    faq_jsx = generate_faq_accordion_jsx(faq_items, styling=config.styling)
    safe_h1 = h1.replace('"', '&quot;')

    return f"""import React from 'react';

export default function {component_name}() {{
  return (
    <main className="min-h-screen bg-white dark:bg-gray-950 py-12 px-4 sm:px-6 lg:px-8">
      <article className="max-w-4xl mx-auto">
        <header className="mb-10">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 uppercase tracking-wider mb-3">
            {cluster} • {page_type}
          </span>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-gray-900 dark:text-white tracking-tight">
            {safe_h1}
          </h1>
        </header>

        <div className="prose prose-lg dark:prose-invert max-w-none">
{body_jsx}
        </div>

{faq_jsx}
      </article>
    </main>
  );
}}
"""


# ============================================================
# STEP 4: WRITE EXPORT FILES & MASTER README
# ============================================================

def export_frontend_components(
    pages: List[Dict[str, Any]],
    config: ExportConfig,
) -> Tuple[int, Path]:
    """
    Compile and export Next.js/React components for all pages into `generated-pages/`.
    """
    ext = "tsx" if config.language == "ts" else "jsx"
    target_base = config.output_dir
    target_base.mkdir(parents=True, exist_ok=True)

    count = 0
    exported_paths: List[Path] = []

    logger.info(f"Compiling {len(pages)} frontend components ({config.framework}, {config.language}, {config.styling})...")

    for p in pages:
        slug = p.get("slug", "untitled").strip("/").replace("/", "-")

        if config.framework == "next-app":
            out_file = target_base / "app" / slug / f"page.{ext}"
            content = build_nextjs_app_router_page(p, config)
        elif config.framework == "next-pages":
            out_file = target_base / "pages" / f"{slug}.{ext}"
            content = build_nextjs_pages_router_page(p, config)
        else:
            out_file = target_base / "components" / f"{slug}.{ext}"
            content = build_react_spa_page(p, config)

        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(content)

        exported_paths.append(out_file)
        count += 1

    # Write a clean instructions README inside the generated-pages directory
    readme_path = target_base / "README.md"
    readme_content = f"""# Generated Frontend Pages

This directory contains **{count} production-ready Next.js / React components** generated by the SEO Automation Agent.

## How to Use in Your Website

### If you are using Next.js App Router (Recommended):
1. Copy the `app/` folder directly into your Next.js project (`src/app/` or root `app/`).
2. Each page is immediately live at its target URL (e.g. `/how-to-get-free-clothes-online/`).
3. SEO metadata, canonical URLs, FAQ accordions, and JSON-LD structured data are pre-configured.

### Features Included:
- **Zero-Config Metadata**: Exported `metadata` objects handle page titles, descriptions, canonicals, and open-graph tags automatically.
- **Google Rich Snippets**: Pre-rendered `<script type="application/ld+json">` tags for Schema.org ({pages[0].get('schema_type', 'Article') if pages else 'Article'}).
- **Native Next.js Links**: Markdown links are converted to `<Link href="...">` components for instant client-side routing.
- **Tailwind Ready**: Styled with standard Tailwind utility classes and `@tailwindcss/typography` prose support.

---
*Generated by SEO Automation Agent on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    logger.info(f"Successfully exported {count} components to: {target_base}")
    return count, target_base


# ============================================================
# STEP 5: INTERACTIVE CLI PROMPT RUNNER
# ============================================================

def prompt_user_for_options() -> ExportConfig:
    """Prompt user in terminal for frontend export preferences with clear defaults."""
    print("\n" + "=" * 60)
    print("[FRONTEND CODE GENERATOR] Next.js & React Component Exporter")
    print("=" * 60)

    # 1. Framework / Router Choice
    print("\n[1/4] Select Target Framework & Router:")
    print("  1) Next.js App Router (app/{slug}/page.tsx) [Recommended / Default]")
    print("  2) Next.js Pages Router (pages/{slug}.tsx)")
    print("  3) Pure React.js (components/{slug}.tsx for Vite / CRA)")
    raw_fw = input("Choice [1-3] (Default: 1): ").strip()
    fw_map = {"1": "next-app", "2": "next-pages", "3": "react-spa"}
    framework = fw_map.get(raw_fw, "next-app")

    # 2. Language Choice
    print("\n[2/4] Select Programming Language:")
    print("  1) TypeScript (.tsx) [Recommended / Default]")
    print("  2) JavaScript (.jsx)")
    raw_lang = input("Choice [1-2] (Default: 1): ").strip()
    language = "js" if raw_lang == "2" else "ts"

    # 3. Styling Approach
    print("\n[3/4] Select Styling Approach:")
    print("  1) Tailwind CSS (uses responsive typography prose classes) [Default]")
    print("  2) Clean Semantic HTML & CSS (zero framework dependencies)")
    raw_style = input("Choice [1-2] (Default: 1): ").strip()
    styling = "semantic" if raw_style == "2" else "tailwind"

    # 4. Output Location
    print("\n[4/4] Output Location:")
    print(f"  1) Dedicated root folder: {DEFAULT_EXPORT_DIR} [Default]")
    print("  2) Custom path on your computer")
    raw_loc = input("Choice [1-2] (Default: 1): ").strip()
    if raw_loc == "2":
        custom_p = input("Enter custom destination directory: ").strip()
        output_dir = Path(custom_p).resolve() if custom_p else DEFAULT_EXPORT_DIR
    else:
        output_dir = DEFAULT_EXPORT_DIR

    print("\n" + "-" * 60)
    print(f"Summary: {framework} | {language.upper()} | {styling.capitalize()} | Output: {output_dir}")
    print("-" * 60 + "\n")

    return ExportConfig(
        framework=framework,
        language=language,
        styling=styling,
        output_dir=output_dir,
    )


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Export SEO Generated Pages to Drop-in Next.js / React Components",
    )
    parser.add_argument(
        "--framework",
        choices=["next-app", "next-pages", "react-spa"],
        default=None,
        help="Target framework (default: interactive prompt or next-app)",
    )
    parser.add_argument(
        "--lang",
        choices=["ts", "js"],
        default=None,
        help="Programming language: ts (.tsx) or js (.jsx)",
    )
    parser.add_argument(
        "--style",
        choices=["tailwind", "semantic"],
        default=None,
        help="Styling system: tailwind or semantic",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"Target export directory (default: {DEFAULT_EXPORT_DIR})",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without prompting in terminal, using defaults or CLI flags",
    )
    parser.add_argument(
        "--pages-dir",
        type=str,
        default=str(OUTPUTS_V03_PAGES_DIR),
        help="Directory containing source {slug}.json and {slug}.md page files",
    )

    args = parser.parse_args()
    configure_logging()

    is_interactive = not (args.non_interactive or (args.framework and args.lang and args.style))

    if is_interactive:
        config = prompt_user_for_options()
    else:
        config = ExportConfig(
            framework=args.framework or "next-app",
            language=args.lang or "ts",
            styling=args.style or "tailwind",
            output_dir=Path(args.output).resolve() if args.output else DEFAULT_EXPORT_DIR,
            non_interactive=True,
        )

    pages_dir = Path(args.pages_dir).resolve()
    pages = load_pages_from_directory(pages_dir)

    count, export_path = export_frontend_components(pages, config)

    print("\n" + "=" * 60)
    print(f"[SUCCESS] {count} Frontend Components generated successfully!")
    print(f"[OUTPUT DIR] {export_path}")
    print("--> Copy the 'app' or 'pages' folder into your Next.js project to publish.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
