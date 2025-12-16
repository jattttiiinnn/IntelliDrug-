
import requests
import json

def test_api():
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        'query.term': 'Diabetes',
        'filter.overallStatus': 'RECRUITING',
        'pageSize': 5
    }
    
    print(f"Fetching {url}...")
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print("Keys:", data.keys())
            if 'studies' in data:
                print(f"Found {len(data['studies'])} studies.")
                print("First study title:", data['studies'][0]['protocolSection']['identificationModule']['officialTitle'])
        else:
            print("Error:", resp.text)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_api()
