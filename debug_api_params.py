
import requests

def test_api_sort():
    url = "https://clinicaltrials.gov/api/v2/studies"
    # Test 1: Just query
    params1 = {
        'query.intr': 'Metformin',
        'pageSize': 5
    }
    print("Test 1 (Basic)...")
    resp = requests.get(url, params=params1)
    print(f"Status: {resp.status_code}")

    # Test 2: With Sort
    params2 = {
        'query.intr': 'Metformin',
        'pageSize': 5,
        'sort': 'date:desc' # Suspect
    }
    print("Test 2 (Sort: date:desc)...")
    resp = requests.get(url, params=params2)
    print(f"Status: {resp.status_code}")
    
    # Test 3: List Filter
    params3 = {
        'query.cond': 'Diabetes',
        'filter.overallStatus': ['RECRUITING', 'ACTIVE_NOT_RECRUITING'],
        'pageSize': 5
    }
    print("Test 3 (List Filter)...")
    resp = requests.get(url, params=params3)
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print("Error content:", resp.text)

if __name__ == "__main__":
    test_api_sort()
