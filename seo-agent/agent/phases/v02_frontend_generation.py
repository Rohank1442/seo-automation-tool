"""
V0.2 — FRONTEND GENERATION

Generates a static frontend scaffold from the completed V0.2 SEO architecture.

Inputs:
    outputs/v02/site_architecture.json
    outputs/v02/url_architecture.json
    outputs/v02/internal_linking.json
    outputs/v02/technical_seo.json

Output:
    outputs/v02/frontend/
"""

import json
from pathlib import Path
from html import escape


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs" / "v02"
FRONTEND_DIR = OUTPUT_DIR / "frontend"

SITE_ARCHITECTURE_FILE = OUTPUT_DIR / "site_architecture.json"
URL_ARCHITECTURE_FILE = OUTPUT_DIR / "url_architecture.json"
INTERNAL_LINKING_FILE = OUTPUT_DIR / "internal_linking.json"
TECHNICAL_SEO_FILE = OUTPUT_DIR / "technical_seo.json"


# ============================================================
# HELPERS
# ============================================================

def load_json(path: Path) -> dict:
    """Load a JSON file and return its contents."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_text(path: Path, content: str) -> None:
    """Save text content to a file, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def normalize_url(url: str) -> str:
    """Normalize a URL path so that it ends with a slash."""
    if not url:
        return "/"

    if not url.startswith("/"):
        url = "/" + url

    if not url.endswith("/"):
        url += "/"

    return url


def url_to_output_path(url: str) -> Path:
    """
    Convert a URL path into a static HTML output path.

    Example:
        /about/ -> about/index.html
        / -> index.html
    """
    url = normalize_url(url)

    if url == "/":
        return FRONTEND_DIR / "index.html"

    relative = url.strip("/")

    return FRONTEND_DIR / relative / "index.html"


def absolute_url(base_url: str, url: str) -> str:
    """Build an absolute URL from the configured base URL."""
    return base_url.rstrip("/") + normalize_url(url)


# ============================================================
# PAGE METADATA
# ============================================================

def build_page_metadata(url_data: dict) -> dict:
    """Extract the metadata required to generate a frontend page."""

    title = url_data.get("title", "")
    url = normalize_url(url_data.get("url", "/"))
    canonical_url = url_data.get("canonical_url", "")

    if not canonical_url:
        canonical_url = absolute_url(
            "https://example.com",
            url
        )

    return {
        "title": title,
        "url": url,
        "canonical_url": canonical_url,
        "page_type": url_data.get("page_type", "content"),
        "primary_keyword": url_data.get("primary_keyword"),
        "indexable": url_data.get("indexable", True),
    }


# ============================================================
# INTERNAL LINKING
# ============================================================

def build_link_map(internal_linking: dict) -> dict:
    """
    Convert the internal-linking architecture into:

        source_page_id -> list of links
    """

    link_map = {}

    for link in internal_linking.get("links", []):
        source = link.get("source_page_id")

        if not source:
            continue

        link_map.setdefault(source, []).append(
            {
                "target_page_id": link.get("target_page_id"),
                "target_url": normalize_url(
                    link.get("target_url", "/")
                ),
                "anchor_text": link.get(
                    "anchor_text",
                    "Read more"
                ),
                "relationship": link.get(
                    "relationship",
                    "related_content"
                ),
                "priority": link.get(
                    "priority",
                    "medium"
                ),
            }
        )

    return link_map


# ============================================================
# HTML
# ============================================================

def generate_navigation(page, pages_by_id):
    """Generate simple navigation links."""

    links = []

    for other_page_id, other_page in pages_by_id.items():

        if other_page_id == page["page_id"]:
            continue

        page_url = normalize_url(other_page["url"])

        links.append(
            f'<a href="{escape(page_url)}">'
            f'{escape(other_page["title"])}'
            f'</a>'
        )

    return "\n".join(links[:10])


def generate_internal_links(page_id, link_map):
    """Generate the contextual internal-link section."""

    links = link_map.get(page_id, [])

    if not links:
        return ""

    html_links = []

    seen = set()

    for link in links:

        target_url = link["target_url"]

        if target_url in seen:
            continue

        seen.add(target_url)

        html_links.append(
            f"""
            <li>
                <a href="{escape(target_url)}">
                    {escape(link["anchor_text"])}
                </a>
            </li>
            """
        )

    return f"""
    <section class="related-content">
        <h2>Related Content</h2>
        <ul>
            {''.join(html_links)}
        </ul>
    </section>
    """


def generate_page_html(
    page,
    page_metadata,
    link_map,
    pages_by_id,
):
    """Generate complete HTML for a single page."""

    title = page_metadata["title"]
    url = page_metadata["url"]
    canonical = page_metadata["canonical_url"]

    description = (
        f"Learn more about {title.lower()} "
        "with practical information, guides, and useful resources."
    )

    robots = (
        "index, follow"
        if page_metadata["indexable"]
        else "noindex, follow"
    )

    page_id = page["page_id"]

    internal_links = generate_internal_links(
        page_id,
        link_map
    )

    navigation = generate_navigation(
        page,
        pages_by_id
    )

    primary_keyword = page_metadata.get(
        "primary_keyword"
    )

    keyword_note = ""

    if primary_keyword:
        keyword_note = f"""
        <p class="keyword-context">
            Primary topic: {escape(primary_keyword)}
        </p>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>{escape(title)}</title>

    <meta
        name="description"
        content="{escape(description)}"
    >

    <meta
        name="robots"
        content="{robots}"
    >

    <link
        rel="canonical"
        href="{escape(canonical)}"
    >

    <!-- Open Graph -->
    <meta
        property="og:title"
        content="{escape(title)}"
    >

    <meta
        property="og:description"
        content="{escape(description)}"
    >

    <meta
        property="og:type"
        content="website"
    >

    <meta
        property="og:url"
        content="{escape(canonical)}"
    >

    <!-- Twitter -->
    <meta
        name="twitter:card"
        content="summary_large_image"
    >

    <meta
        name="twitter:title"
        content="{escape(title)}"
    >

    <meta
        name="twitter:description"
        content="{escape(description)}"
    >

    <!-- Structured Data Placeholder -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": {json.dumps(title)},
        "url": {json.dumps(canonical)}
    }}
    </script>

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            line-height: 1.7;
            color: #222;
            background: #fff;
        }}

        header {{
            border-bottom: 1px solid #ddd;
            padding: 20px;
        }}

        nav {{
            max-width: 1100px;
            margin: auto;
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
        }}

        nav a {{
            text-decoration: none;
            color: #333;
        }}

        main {{
            max-width: 900px;
            margin: 50px auto;
            padding: 0 20px;
        }}

        h1 {{
            font-size: 42px;
            line-height: 1.2;
        }}

        h2 {{
            margin-top: 40px;
        }}

        .intro {{
            font-size: 19px;
            color: #555;
        }}

        .related-content {{
            margin-top: 50px;
            padding-top: 30px;
            border-top: 1px solid #ddd;
        }}

        .related-content li {{
            margin: 10px 0;
        }}

        footer {{
            margin-top: 80px;
            padding: 30px 20px;
            background: #f5f5f5;
        }}

        footer p {{
            max-width: 1100px;
            margin: auto;
        }}

        .keyword-context {{
            font-size: 14px;
            color: #777;
        }}
    </style>
</head>

<body>

<header>
    <nav>
        {navigation}
    </nav>
</header>

<main>

    <article>

        <h1>{escape(title)}</h1>

        <p class="intro">
            This page is part of the Virtual Try-On Tech
            content cluster.
        </p>

        {keyword_note}

        <section>
            <h2>Overview</h2>

            <p>
                Content for this page will be generated in
                the content-generation phase.
            </p>
        </section>

        {internal_links}

    </article>

</main>

<footer>
    <p>
        Generated by the SEO Automation Agent — V0.2
    </p>
</footer>

</body>
</html>
"""


# ============================================================
# ROBOTS.TXT
# ============================================================

def generate_robots_txt(technical_seo: dict) -> str:
    """Generate robots.txt from the technical SEO specification."""

    robots_data = technical_seo.get("robots_txt", {})

    content = robots_data.get("content")

    if content:
        return content

    return (
        "User-agent: *\n"
        "Allow: /\n\n"
        "Sitemap: https://example.com/sitemap.xml\n"
    )


# ============================================================
# SITEMAP
# ============================================================

def generate_sitemap(technical_seo: dict) -> str:
    """Generate sitemap.xml from the technical SEO specification."""

    sitemap = technical_seo.get("sitemap", {})

    urls = sitemap.get("urls", [])

    entries = []

    for item in urls:

        url = item.get("url")

        if not url:
            continue

        changefreq = item.get(
            "changefreq",
            "monthly"
        )

        priority = item.get(
            "priority",
            0.7
        )

        entries.append(
            f"""
    <url>
        <loc>{escape(url)}</loc>
        <changefreq>{escape(str(changefreq))}</changefreq>
        <priority>{priority}</priority>
    </url>
            """
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>

<urlset
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
>
{''.join(entries)}
</urlset>
"""


# ============================================================
# VALIDATION
# ============================================================

def validate_generated_pages(
    pages,
    link_map,
):
    """Validate that all architecture pages were generated."""

    errors = []

    for page in pages:

        output_path = url_to_output_path(
            page["url"]
        )

        if not output_path.exists():
            errors.append(
                f"Missing generated page: {output_path}"
            )

    return errors


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("        V0.2 — FRONTEND GENERATION")
    print("=" * 60)

    # --------------------------------------------------------
    # Step 1
    # --------------------------------------------------------

    print("\n[Step 1] Loading site architecture...")

    site_architecture = load_json(
        SITE_ARCHITECTURE_FILE
    )

    print("  ✓ Site architecture loaded")

    # --------------------------------------------------------
    # Step 2
    # --------------------------------------------------------

    print("\n[Step 2] Loading URL architecture...")

    url_architecture = load_json(
        URL_ARCHITECTURE_FILE
    )

    print("  ✓ URL architecture loaded")

    # --------------------------------------------------------
    # Step 3
    # --------------------------------------------------------

    print("\n[Step 3] Loading internal linking architecture...")

    internal_linking = load_json(
        INTERNAL_LINKING_FILE
    )

    print("  ✓ Internal linking architecture loaded")

    # --------------------------------------------------------
    # Step 4
    # --------------------------------------------------------

    print("\n[Step 4] Loading technical SEO architecture...")

    technical_seo = load_json(
        TECHNICAL_SEO_FILE
    )

    print("  ✓ Technical SEO architecture loaded")

    # --------------------------------------------------------
    # Step 5
    # --------------------------------------------------------

    print("\n[Step 5] Preparing page metadata...")

    pages = url_architecture.get("urls", [])

    pages_by_id = {
        page["page_id"]: page
        for page in pages
    }

    metadata = {
        page["page_id"]: build_page_metadata(page)
        for page in pages
    }

    print(f"  ✓ Prepared {len(pages)} pages")

    # --------------------------------------------------------
    # Step 6
    # --------------------------------------------------------

    print("\n[Step 6] Preparing internal links...")

    link_map = build_link_map(
        internal_linking
    )

    total_links = sum(
        len(links)
        for links in link_map.values()
    )

    print(f"  ✓ Loaded {total_links} internal links")

    # --------------------------------------------------------
    # Step 7
    # --------------------------------------------------------

    print("\n[Step 7] Generating frontend pages...")

    generated_pages = []

    for page in pages:

        page_id = page["page_id"]

        html = generate_page_html(
            page,
            metadata[page_id],
            link_map,
            pages_by_id,
        )

        output_path = url_to_output_path(
            page["url"]
        )

        save_text(
            output_path,
            html
        )

        generated_pages.append(
            str(output_path)
        )

    print(
        f"  ✓ Generated {len(generated_pages)} HTML pages"
    )

    # --------------------------------------------------------
    # Step 8
    # --------------------------------------------------------

    print("\n[Step 8] Generating robots.txt...")

    robots_content = generate_robots_txt(
        technical_seo
    )

    save_text(
        FRONTEND_DIR / "robots.txt",
        robots_content
    )

    print("  ✓ robots.txt generated")

    # --------------------------------------------------------
    # Step 9
    # --------------------------------------------------------

    print("\n[Step 9] Generating sitemap.xml...")

    sitemap_content = generate_sitemap(
        technical_seo
    )

    save_text(
        FRONTEND_DIR / "sitemap.xml",
        sitemap_content
    )

    print("  ✓ sitemap.xml generated")

    # --------------------------------------------------------
    # Step 10
    # --------------------------------------------------------

    print("\n[Step 10] Validating generated frontend...")

    errors = validate_generated_pages(
        pages,
        link_map
    )

    if errors:

        print("\n  ✗ Validation failed:")

        for error in errors:
            print(f"    - {error}")

        raise RuntimeError(
            "Frontend generation validation failed."
        )

    print("  ✓ All pages generated successfully")
    print("  ✓ Frontend architecture is valid")

    # --------------------------------------------------------
    # Step 11
    # --------------------------------------------------------

    manifest = {
        "version": "0.2",
        "architecture_type": "frontend_generation",
        "site_status": url_architecture.get(
            "site_status",
            "brand_new"
        ),
        "output_directory": str(
            FRONTEND_DIR
        ),
        "summary": {
            "total_pages": len(pages),
            "generated_pages": len(generated_pages),
            "internal_links": total_links,
            "robots_txt": True,
            "sitemap": True,
            "validation_status": "valid",
        },
        "pages": [
            {
                "page_id": page["page_id"],
                "title": page["title"],
                "url": normalize_url(
                    page["url"]
                ),
                "output": str(
                    url_to_output_path(
                        page["url"]
                    )
                ),
            }
            for page in pages
        ],
        "source_files": {
            "site_architecture": str(
                SITE_ARCHITECTURE_FILE
            ),
            "url_architecture": str(
                URL_ARCHITECTURE_FILE
            ),
            "internal_linking": str(
                INTERNAL_LINKING_FILE
            ),
            "technical_seo": str(
                TECHNICAL_SEO_FILE
            ),
        },
    }

    save_text(
        OUTPUT_DIR / "frontend_generation.json",
        json.dumps(
            manifest,
            indent=2
        )
    )

    # --------------------------------------------------------
    # Complete
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("        FRONTEND GENERATION COMPLETE")
    print("=" * 60)

    print(
        f"\nGenerated frontend: {FRONTEND_DIR}"
    )

    print(
        "Manifest: outputs/v02/frontend_generation.json"
    )


if __name__ == "__main__":
    main()