import requests
import json

def test_patentsview_v2():
    # Attempting various potential endpoints
    endpoints = [
        "https://search.patentsview.org/api/v1/patent/",
        "https://api.patentsview.org/patents/query"
    ]
    
    query = {"q": {"_text_phrase": {"patent_title": "Metformin"}}}
    
    for url in endpoints:
        print(f"\nTesting {url}...")
        try:
            if "query" in url:
                # V1 Style
                params = {"q": json.dumps(query)}
                response = requests.get(url, params=params, timeout=10)
            else:
                # V2 Style might be POST or different structure
                # Try simple GET first
                response = requests.get(url, params={"q": "Metformin"}, timeout=10)
                
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("Success!")
                print(response.text[:200])
                break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_patentsview_v2()
