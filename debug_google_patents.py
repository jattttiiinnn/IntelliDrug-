import requests
from bs4 import BeautifulSoup

def test_google_patents():
    url = "https://patents.google.com/"
    params = {"q": "Metformin"}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Fetching {url} with params {params}...")
    response = requests.get(url, params=params, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Google Patents usually loads results dynamically, but let's see if we get anything
        # Look for result items
        results = soup.find_all('search-result-item')
        print(f"Found {len(results)} 'search-result-item' elements.")
        
        # Check for any articles or common classes
        articles = soup.find_all('article')
        print(f"Found {len(articles)} 'article' elements.")
        
        # Save to file to inspect
        with open("debug_patents.html", "w", encoding="utf-8") as f:
            f.write(response.text)
            
if __name__ == "__main__":
    test_google_patents()
