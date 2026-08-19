from ddgs import DDGS

query = "Festival and Concert Outfits"

with DDGS() as ddgs:
    results = list(ddgs.text(
        query,
        max_results=5
    ))

print(results)