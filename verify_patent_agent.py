import asyncio
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from agents.patent_agent import PatentAgent

async def test_search():
    agent = PatentAgent()
    print("\n--- Testing Patent Search for 'Metformin' ---")
    
    # 1. Search
    results = agent.search_patents_by_molecule("Metformin")
    print(f"Found {len(results)} patents.")
    
    if not results:
        print("No patents found. Check API or Query.")
        return

    # 2. Inspect First Result
    top = results[0]
    print(f"Top Patent: {top.patent_number}")
    print(f"Title: {top.title}")
    print(f"Assignee: {top.assignee}")
    print(f"Status: {top.status}")
    print(f"Abstract: {top.abstract[:100]}...")

    # 3. Test Analysis (Gemini)
    print("\n--- Testing Async Analysis ---")
    analysis = await agent.analyze_async("Metformin")
    print(f"FTO Status: {analysis.get('fto_status')}")
    print(f"Confidence: {analysis.get('confidence')}")
    print(f"Key Findings: {len(analysis.get('findings', []))}")
    print(f"Top 5 Patents returned: {len(analysis.get('top_patents', []))}")

if __name__ == "__main__":
    asyncio.run(test_search())
