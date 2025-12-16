
import requests
from bs4 import BeautifulSoup

def debug_scrape():
    url = "https://clinicaltrials.gov/search"
    params = {
        'term': 'Metformin',
        # 'aggFilters': 'status:rec status:act status:enr',
        # Try simplified params first
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"Fetching {url}...")
    resp = requests.get(url, params=params, headers=headers)
    print(f"Status: {resp.status_code}")
    
    with open("debug_ct.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    cards = soup.find_all('div', class_='study-info')
    print(f"Found {len(cards)} cards with class 'study-info'")
    
    # Check for new UI classes if any
    # New CT.gov might use different classes
    
    # Check for 'results-list-card' (common in other scrapers for CT.gov)
    other_cards = soup.find_all('div', class_='results-list-card')
    print(f"Found {len(other_cards)} cards with class 'results-list-card'")

if __name__ == "__main__":
    debug_scrape()
