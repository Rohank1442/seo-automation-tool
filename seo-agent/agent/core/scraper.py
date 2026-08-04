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
        if response.status_code == 200:
            data = response.json()
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
            "num": max_results
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
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
            for r in results:
                if 'link' in r:
                    urls.append(r['link'])
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
        "word_count": 0,
        "error": None
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
        result["h1s"] = [h1.get_text().strip() for h1 in soup.find_all("h1") if h1.get_text().strip()]
        
        # 3. H2/H3 structure
        for heading in soup.find_all(["h2", "h3"]):
            text = heading.get_text().strip()
            if text:
                result["headings"].append({
                    "tag": heading.name,
                    "text": text
                })
                
        # 4. Word count estimation
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        # Clean whitespace and count words
        words = re.findall(r'\b\w+\b', text)
        result["word_count"] = len(words)
        
    except Exception as e:
        result["error"] = str(e)
        
    return result

def get_dataforseo_metrics(keywords: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Query DataForSEO API for search volume and keyword difficulty.
    Returns mapping of keyword -> {volume, difficulty}.
    """
    metrics = {}
    if not DATAFORSEO_LOGIN or not DATAFORSEO_PASSWORD:
        return metrics
        
    url = "https://api.dataforseo.com/v3/keywords_data/google/search_volume/live"
    # DataForSEO allows up to 700 keywords per request
    # We will process them in chunks of 500
    chunk_size = 500
    for i in range(0, len(keywords), chunk_size):
        chunk = keywords[i:i + chunk_size]
        payload = [
            {
                "keywords": chunk,
                "location_code": 2840,  # US
                "language_code": "en"
            }
        ]
        try:
            # Note: Basic auth uses base64 encoded user:pass
            response = requests.post(
                url, 
                auth=(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD),
                json=payload, 
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                tasks = data.get("tasks", [])
                for task in tasks:
                    results = task.get("result", [])
                    for res in results:
                        kw = res.get("keyword")
                        metrics[kw] = {
                            "volume": res.get("search_volume", 0),
                            "difficulty": res.get("competition_level", 0) # or custom metric
                        }
        except Exception as e:
            print(f"DataForSEO API call failed: {e}")
            
    return metrics
