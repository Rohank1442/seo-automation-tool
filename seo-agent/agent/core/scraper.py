import json
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from duckduckgo_search import DDGS
from core.config import SERPAPI_API_KEY, DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD

# Standard headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_google_autocomplete(query: str) -> List[str]:
    """
    Fetch search suggestions from Google Autocomplete endpoint.
    Returns list of matching queries.
    """
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={requests.utils.quote(query)}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        print(f"Fetching autocomplete for '{query}' from Google: {response.json()}")
        if response.status_code == 200:
            data = response.json()
            print(
                f"Autocomplete data for ----------- in google seach autocomplete '{query}': {data}"
            )
            # The structure is: [query, [suggestions...], ...]
            if len(data) > 1 and isinstance(data[1], list):
                return data[1]
    except Exception as e:
        print(f"Error fetching autocomplete for '{query}': {e}")
    return []


def get_competitor_urls(query: str, max_results: int = 5) -> List[str]:
    """
    Find top ranking page URLs for a query.
    Tries SerpApi if configured, otherwise falls back to DuckDuckGo search.
    """
    if SERPAPI_API_KEY:
        url = "https://serpapi.com/search.json"
        params = {
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "engine": "google",
            "num": max_results,
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                print(f"SerpApi results for '{query}': {data}")
                results = data.get("organic_results", [])
                urls = [item["link"] for item in results if "link" in item]
                return urls[:max_results]
        except Exception as e:
            print(f"SerpApi query failed: {e}. Falling back to DuckDuckGo.")

    # Free fallback using DuckDuckGo
    try:
        urls = []
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            print(f"DuckDuckGo results for '{query}': {results}")
            for r in results:
                link = r.get("href") or r.get("link")

                if link:
                    urls.append(link)
        print(f"Filtered URLs for '{query}': {urls}")
        return urls[:max_results]
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")
        return []


def crawl_competitor_page(url: str) -> Dict[str, Any]:
    """
    Crawl a competitor URL and extract structured content outlines.
    """
    result = {
        "url": url,
        "title": "",
        "h1s": [],
        "headings": [],
        "questions": [],
        "word_count": 0,
        "error": None,
    }
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # 1. Title
        title_tag = soup.find("title")
        if title_tag:
            result["title"] = title_tag.get_text().strip()

        # 2. H1s
        result["h1s"] = [
            h1.get_text().strip() for h1 in soup.find_all("h1") if h1.get_text().strip()
        ]

        # 3. H2/H3 structure and FAQ questions
        for heading in soup.find_all(["h2", "h3"]):
            text = heading.get_text().strip()
            if text:
                result["headings"].append({"tag": heading.name, "text": text})
                if text.endswith("?"):
                    result["questions"].append(text)

        # 4. Word count estimation
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        # Clean whitespace and count words
        words = re.findall(r"\b\w+\b", text)
        result["word_count"] = len(words)
        print(f"Word count for '{url}': {result['word_count']}")

    except Exception as e:
        result["error"] = str(e)

    return result


def get_dataforseo_metrics(
    keywords: List[str],
) -> Dict[str, Dict[str, Any]]:
    """
    Query DataForSEO for Google keyword metrics.

    Returns:
        {
            "keyword": {
                "volume": int | None,
                "competition": float | None,
                "competition_level": str | None,
                "cpc": float | None,
                "source": "dataforseo",
            }
        }

    If DataForSEO is unavailable or fails, returns whatever
    metrics were successfully retrieved. The caller can continue
    processing all keywords regardless.
    """

    metrics: Dict[str, Dict[str, Any]] = {}

    if not DATAFORSEO_LOGIN or not DATAFORSEO_PASSWORD:
        print("  • DataForSEO credentials not configured. Skipping metrics.")
        return metrics

    if not keywords:
        return metrics

    url = "https://api.dataforseo.com/v3/keywords_data/google/search_volume/live"

    # API supports up to 700 keywords per request.
    chunk_size = 500

    for i in range(0, len(keywords), chunk_size):
        chunk = keywords[i : i + chunk_size]

        payload = [
            {
                "keywords": chunk,
                "location_code": 2840,  # United States
                "language_code": "en",
            }
        ]

        try:
            response = requests.post(
                url,
                auth=(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD),
                json=payload,
                timeout=30,
            )

            print(
                f"  • DataForSEO chunk "
                f"{i + 1}-{i + len(chunk)}: "
                f"HTTP {response.status_code}"
            )

            # HTTP-level failure
            if response.status_code != 200:
                print(f"    - DataForSEO HTTP error: " f"{response.status_code}")
                print(f"    - Response: {response.text[:500]}")
                continue

            data = response.json()

            # API-level failure
            if data.get("status_code") != 20000:
                print(
                    f"    - DataForSEO API error: "
                    f"{data.get('status_code')} - "
                    f"{data.get('status_message')}"
                )
                continue

            tasks = data.get("tasks", [])

            for task in tasks:

                # Individual task failure
                if task.get("status_code") != 20000:
                    print(
                        f"    - DataForSEO task error: "
                        f"{task.get('status_code')} - "
                        f"{task.get('status_message')}"
                    )
                    continue

                results = task.get("result") or []

                for result in results:
                    keyword = result.get("keyword")

                    if not keyword:
                        continue

                    metrics[keyword.lower()] = {
                        "volume": result.get("search_volume"),
                        "competition": result.get("competition"),
                        "competition_level": result.get("competition_level"),
                        "cpc": result.get("cpc"),
                        "source": "dataforseo",
                    }

            print(f"    - Metrics received: " f"{len(metrics)} total")

        except requests.RequestException as e:
            print(f"    - DataForSEO request failed: {e}")

        except ValueError as e:
            print(f"    - Invalid JSON from DataForSEO: {e}")

        except Exception as e:
            print(f"    - Unexpected DataForSEO error: {e}")

    return metrics


def get_people_also_ask(query: str) -> List[str]:
    """
    Fetch People Also Ask questions for a query.
    Requires SerpApi. If SerpApi is not configured or fails, returns an empty list.
    """
    if not SERPAPI_API_KEY:
        return []

    url = "https://serpapi.com/search.json"
    params = {"q": query, "api_key": SERPAPI_API_KEY, "engine": "google", "num": 5}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            paa_items = data.get("people_also_ask", [])
            questions = [item["question"] for item in paa_items if "question" in item]
            return questions
    except Exception as e:
        print(f"SerpApi PAA fetch failed: {e}")
    return []


def get_ddg_related_searches(query: str) -> List[str]:
    """
    Fetch related queries / suggestions from DuckDuckGo's autocomplete endpoint.
    """
    url = f"https://ac.duckduckgo.com/ac/?q={requests.utils.quote(query)}&type=list"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(
                f"-------------------------- DuckDuckGo autocomplete data for '{query}': {data}"
            )
            if len(data) > 1 and isinstance(data[1], list):
                return data[1]
    except Exception as e:
        print(
            f"DuckDuckGo direct suggestions fetch failed for '{query}': {e}. Trying library fallback..."
        )

    # Library fallback
    try:
        suggestions = []
        with DDGS() as ddgs:
            results = ddgs.suggestions(query)
            for r in results:
                if isinstance(r, dict) and "phrase" in r:
                    suggestions.append(r["phrase"])
                elif isinstance(r, str):
                    suggestions.append(r)
        return suggestions
    except Exception as e:
        print(f"DuckDuckGo suggestions library failed: {e}")
    return []
