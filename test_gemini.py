# import pandas as pd
# df = pd.read_csv('data/molecules.csv')
# print(df.head()) 

# from data_utils import get_molecule_info

# info = get_molecule_info("Metformin")
# print(info)

# from agents.patent_agent import PatentAgent

# agent = PatentAgent()
# result = agent.search_patent("Metformin")
# print(result)

# from master_agent import MasterAgent

# master = MasterAgent()
# result = master.analyze_repurposing("Metformin", "NASH")
# print(result)

# from agents.web_intelligence_agent import WebIntelligenceAgent

# agent = WebIntelligenceAgent()
# result = agent.analyze("Metformin", "NASH")

# print(f"Literature Support: {result['literature_support']}")
# print(f"Key Findings: {result['key_findings']}")
# print(f"Confidence: {result['confidence']}")

# from agents.exim_agent import EXIMAgent

# agent = EXIMAgent()
# result = agent.analyze_sourcing("Metformin")

# print(f"Import Dependency: {result['import_dependency']}")
# print(f"Sourcing Risk: {result['sourcing_risk']}")
# print(f"Manufacturing Viability: {result['manufacturing_viability']}")

# from agents.internal_knowledge_agent import InternalKnowledgeAgent

# agent = InternalKnowledgeAgent()
# result = agent.analyze("Metformin", "PCOS")

# print(f"Past Experience: {result['past_experience']}")
# print(f"Manufacturing: {result['manufacturing_capability']}")
# print(f"Strategic Alignment: {result['strategic_alignment']}")

# from agents.report_generator_agent import ReportGeneratorAgent

# # Mock results from all agents
# mock_results = {
#     "molecule": "Metformin",
#     "disease": "NASH",
#     "patent_analysis": {"molecule": "Metformin",
#         "patent_status": "Active",
#         "expiry_date": "2026",
#         "fto_status": "Risk",
#         "confidence": 0.95,
#         "reasoning": "Mock reasoning for patent status."},
#     "clinical_trials_analysis": {"active_trials": 3,
#         "phases": {"phase_1": 1, "phase_2": 2, "phase_3": 0},
#         "key_sponsors": ["PharmaNova Ltd."],
#         "latest_findings": "Mock summary of clinical trials.",
#         "confidence": 0.9},
#     # ... other agent results
#     "overall_recommendation": "PROCEED",
#     "overall_confidence": 0.87
# }

# generator = ReportGeneratorAgent()
# pdf_path = generator.generate_report(
#     "Metformin", 
#     "NASH", 
#     mock_results
# )

# print(f"Report generated: {pdf_path}")

import asyncio
from agents.patent_agent import PatentAgent

# Test sync
agent = PatentAgent()
result = agent.analyze("Metformin", "NASH")
print("Sync works:", result.get("patent_status"))

# Test async
async def test_async():
    result = await agent.analyze_async("Metformin", "NASH")
    print("Async works:", result.get("patent_status"))

asyncio.run(test_async())