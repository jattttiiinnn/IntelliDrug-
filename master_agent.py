# """
# master_agent.py

# MasterAgent orchestrates PatentAgent, ClinicalTrialsAgent, and MarketAgent
# and provides an intelligent synthesis for drug repurposing recommendations.
# """

# from __future__ import annotations
# import json
# import logging
# from datetime import datetime
# from typing import Dict, Any
# from dotenv import load_dotenv
# import google.generativeai as genai

# # Worker agents
# from agents.patent_agent import PatentAgent
# from agents.clinical_trials_agent import ClinicalTrialsAgent
# from agents.market_agent import MarketAgent
# from conflict_detector import ConflictDetector


# # Configure basic logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s"
# )


# class MasterAgent:
#     """
#     Master agent coordinating multiple worker agents for drug repurposing analysis
#     and providing synthesized recommendation.
#     """

#     def __init__(self) -> None:
#         load_dotenv()
#         api_key = genai.api_key if hasattr(genai, "api_key") else None
#         if not api_key:
#             api_key = genai.configure(api_key=None)
#         self.patent_agent = PatentAgent()
#         self.trials_agent = ClinicalTrialsAgent()
#         self.market_agent = MarketAgent()

#     def analyze_repurposing(self, molecule_name: str, disease_name: str) -> dict:
#         """
#         Run all worker agents and combine their outputs, including synthesized recommendation.
#         """
#         logging.info(f"Starting analysis for molecule '{molecule_name}' and disease '{disease_name}'")

#         # Patent analysis
#         print("[1/3] Running PatentAgent...")
#         logging.info("Running PatentAgent")
#         try:
#             patent_result = self.patent_agent.search_patent(molecule_name)
#         except Exception as e:
#             logging.error(f"PatentAgent failed: {e}")
#             patent_result = {"error": str(e)}

#         # Clinical trials analysis
#         print("[2/3] Running ClinicalTrialsAgent...")
#         logging.info("Running ClinicalTrialsAgent")
#         try:
#             clinical_result = self.trials_agent.search_trials(molecule_name, disease_name)
#         except Exception as e:
#             logging.error(f"ClinicalTrialsAgent failed: {e}")
#             clinical_result = {"error": str(e)}

#         # Market analysis
#         print("[3/3] Running MarketAgent...")
#         logging.info("Running MarketAgent")
#         try:
#             market_result = self.market_agent.analyze_market(disease_name)
#         except Exception as e:
#             logging.error(f"MarketAgent failed: {e}")
#             market_result = {"error": str(e)}

#         timestamp = datetime.utcnow().isoformat() + "Z"

#         all_results = {
#             "molecule": molecule_name,
#             "disease": disease_name,
#             "patent_analysis": patent_result,
#             "clinical_analysis": clinical_result,
#             "market_analysis": market_result,
#             "timestamp": timestamp
#         }

#         # Synthesize recommendation
#         print("[4/4] Synthesizing overall recommendation...")
#         logging.info("Synthesizing results")
#         try:
#             synthesis = self.synthesize_results(all_results)
#         except Exception as e:
#             logging.error(f"Synthesis failed: {e}")
#             synthesis = {"error": str(e)}

#         all_results["synthesis"] = synthesis
#         logging.info("Analysis complete.")
#         return all_results

#     def synthesize_results(self, all_results: dict) -> dict:
#         """
#         Use Gemini API to synthesize a combined recommendation based on all analyses.

#         Returns:
#             dict: {
#                 'overall_confidence': float,
#                 'recommendation': str,   # PROCEED / CAUTION / REJECT
#                 'key_factors': list[str],
#                 'risks': list[str],
#                 'next_steps': str
#             }
#         """
#         # Prepare prompt with JSON data
#         prompt = (
#             f"You are a drug development strategist. Given these analyses:\n\n"
#             f"Patent: {json.dumps(all_results['patent_analysis'])}\n"
#             f"Clinical Trials: {json.dumps(all_results['clinical_analysis'])}\n"
#             f"Market: {json.dumps(all_results['market_analysis'])}\n\n"
#             f"Synthesize a recommendation for repurposing {all_results['molecule']} for {all_results['disease']}.\n"
#             f"Consider patent risk, clinical evidence, and market opportunity.\n"
#             f"Output JSON with the following structure:\n"
#             f"{{"
#             f"'overall_confidence': float,"
#             f"'recommendation': str,"
#             f"'key_factors': list[str],"
#             f"'risks': list[str],"
#             f"'next_steps': str"
#             f"}}"
#         )

#         # Call Gemini API
#         try:
#             response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
#         except Exception as e:
#             raise RuntimeError(f"Gemini API request failed during synthesis: {e}")

#         if not response or not hasattr(response, "text"):
#             raise RuntimeError("Gemini API returned an empty response during synthesis.")

#         raw_output = response.text.strip()

#         # Clean Markdown fences
#         import re
#         clean_output = re.sub(
#             r"^```(?:json)?|```$",
#             "",
#             raw_output.strip(),
#             flags=re.IGNORECASE | re.MULTILINE,
#         ).strip()

#         # Parse JSON
#         try:
#             result = json.loads(clean_output)
#         except json.JSONDecodeError:
#             raise RuntimeError(f"Failed to parse Gemini synthesis output as JSON: {raw_output}")

#         # Validate keys
#         required_keys = {"overall_confidence", "recommendation", "key_factors", "risks", "next_steps"}
#         missing = required_keys - set(result.keys())
#         if missing:
#             raise RuntimeError(f"Synthesis JSON missing keys: {missing}")

#         conflict_report = ConflictDetector.detect_conflicts(all_results)
#         if conflict_report.get("conflict_detected"):
#             # Add conflict info to the result JSON
#             result["conflict_alert"] = conflict_report

#         return result

# import asyncio
# import logging
# from datetime import datetime
# from typing import Any, Dict, List

# from agents.patent_agent import PatentAgent
# from agents.clinical_trials_agent import ClinicalTrialsAgent
# from agents.market_agent import MarketAgent
# from agents.web_intelligence_agent import WebIntelligenceAgent
# from agents.exim_agent import EXIMAgent
# from agents.internal_knowledge_agent import InternalKnowledgeAgent
# from agents.report_generator_agent import ReportGeneratorAgent

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# class MasterAgent:
#     """
#     Orchestrates all analysis agents for drug repurposing
#     and synthesizes the results into a holistic recommendation.
#     """

#     def __init__(self):
#         self.patent_agent = PatentAgent()
#         self.clinical_agent = ClinicalTrialsAgent()
#         self.market_agent = MarketAgent()
#         self.web_agent = WebIntelligenceAgent()
#         self.exim_agent = EXIMAgent()
#         self.internal_agent = InternalKnowledgeAgent()
#         self.report_generator = ReportGeneratorAgent()

#         self.progress: Dict[str, str] = {
#             "PatentAgent": "Pending",
#             "ClinicalTrialsAgent": "Pending",
#             "MarketAgent": "Pending",
#             "WebIntelligenceAgent": "Pending",
#             "EXIMAgent": "Pending",
#             "InternalKnowledgeAgent": "Pending",
#             "ReportGeneratorAgent": "Pending",
#         }

#     def get_analysis_progress(self) -> Dict[str, str]:
#         """Returns current status of each agent."""
#         return self.progress

#     async def _run_agent(self, name: str, func, *args, **kwargs) -> Any:
#         """Helper to run an agent method asynchronously with error handling."""
#         self.progress[name] = "Running"
#         try:
#             result = await asyncio.to_thread(func, *args, **kwargs)
#             self.progress[name] = "Complete"
#             logger.info(f"{name} completed successfully.")
#             return result
#         except Exception as e:
#             self.progress[name] = "Failed"
#             logger.error(f"{name} failed: {e}")
#             return {"error": str(e), "confidence": 0.0}

#     async def analyze_repurposing(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
#         """
#         Coordinates all 6 analysis agents, synthesizes results, and generates PDF report.

#         Returns a comprehensive dictionary of results including the PDF path.
#         """
#         logger.info(f"Starting analysis for molecule '{molecule_name}' and disease '{disease_name}'.")

#         # Run all agents in parallel
#         tasks = {
#             "patent_analysis": self._run_agent("PatentAgent", self.patent_agent.search_patent, molecule_name),
#             "clinical_analysis": self._run_agent("ClinicalTrialsAgent", self.clinical_agent.search_trials, molecule_name, disease_name),
#             "market_analysis": self._run_agent("MarketAgent", self.market_agent.analyze_market, disease_name),
#             "web_analysis": self._run_agent("WebIntelligenceAgent", self.web_agent.analyze, molecule_name, disease_name),
#             "exim_analysis": self._run_agent("EXIMAgent", self.exim_agent.analyze_sourcing, molecule_name),
#             "internal_analysis": self._run_agent("InternalKnowledgeAgent", self.internal_agent.analyze, molecule_name, disease_name),
#         }

#         results = await asyncio.gather(*tasks.values())
#         all_results = dict(zip(tasks.keys(), results))
#         all_results["molecule"] = molecule_name
#         all_results["disease"] = disease_name
#         all_results["timestamp"] = datetime.utcnow().isoformat() + "Z"

#         # Synthesize results
#         synthesis = await self._run_agent("MasterSynthesis", self.synthesize_results, all_results)
#         all_results["master_synthesis"] = synthesis

#         # Generate PDF report
#         pdf_task = await self._run_agent(
#             "ReportGeneratorAgent",
#             self.report_generator.generate_report,
#             molecule_name,
#             disease_name,
#             all_results,
#         )
#         all_results["pdf_report"] = pdf_task.get("pdf_path") if isinstance(pdf_task, dict) else pdf_task

#         logger.info("Analysis complete.")
#         return all_results

#     def synthesize_results(self, all_agent_results: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Uses Gemini API to synthesize findings from all 6 agents and
#         provide a holistic recommendation with weighted confidence.
#         """
#         # Weights for confidence aggregation
#         weights = {
#             "patent_analysis": 0.25,
#             "clinical_analysis": 0.20,
#             "market_analysis": 0.20,
#             "web_analysis": 0.15,
#             "exim_analysis": 0.10,
#             "internal_analysis": 0.10,
#         }

#         overall_confidence = 0.0
#         for agent, weight in weights.items():
#             conf = all_agent_results.get(agent, {}).get("confidence", 0.0)
#             overall_confidence += conf * weight

#         # Determine recommendation based on thresholds
#         if overall_confidence >= 0.75:
#             recommendation = "PROCEED"
#         elif overall_confidence >= 0.5:
#             recommendation = "CAUTION"
#         else:
#             recommendation = "REJECT"

#         # Extract key factors, risks, opportunities, next steps
#         key_factors = []
#         risks = []
#         opportunities = []
#         next_steps = []

#         for agent_name, result in all_agent_results.items():
#             if not isinstance(result, dict):
#                 continue
#             # Append meaningful fields
#             if agent_name == "patent_analysis":
#                 key_factors.append(f"Patent status: {result.get('patent_status')}")
#                 if result.get("fto_status") == "Risk":
#                     risks.append("Potential patent infringement")
#             if agent_name == "clinical_analysis":
#                 key_factors.append(f"Active trials: {result.get('active_trials')}")
#                 opportunities.append(f"Phase distribution: {result.get('phases')}")
#             if agent_name == "market_analysis":
#                 key_factors.append(f"Market opportunity: {result.get('opportunity_score')}")
#             if agent_name == "web_analysis":
#                 key_factors.append(f"Literature support: {result.get('literature_support')}")
#             if agent_name == "exim_analysis":
#                 key_factors.append(f"Sourcing risk: {result.get('sourcing_risk')}")
#             if agent_name == "internal_analysis":
#                 key_factors.append(f"Strategic alignment: {result.get('strategic_alignment')}")

#         # Mock next steps & investment estimate
#         next_steps.append("Proceed to preclinical evaluation")
#         next_steps.append("Engage regulatory team")
#         estimated_timeline = "12-18 months"
#         estimated_investment = "$5-8M"

#         return {
#             "overall_confidence": round(overall_confidence, 2),
#             "recommendation": recommendation,
#             "key_factors": key_factors,
#             "risks": risks,
#             "opportunities": opportunities,
#             "next_steps": next_steps,
#             "estimated_timeline": estimated_timeline,
#             "estimated_investment": estimated_investment,
#         }

# master_agent.py
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from agents.patent_agent import PatentAgent
from agents.clinical_trials_agent import ClinicalTrialsAgent
from agents.market_agent import MarketAgent
from agents.web_intelligence_agent import WebIntelligenceAgent
from agents.exim_agent import EXIMAgent
from agents.internal_knowledge_agent import InternalKnowledgeAgent
from agents.report_generator_agent import ReportGeneratorAgent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class MasterAgent:
    """
    Orchestrates all analysis agents in parallel using asyncio.
    """

    def __init__(self):
        self.agents = {
            "patent_analysis": PatentAgent(),
            "clinical_analysis": ClinicalTrialsAgent(),
            "market_analysis": MarketAgent(),
            "web_analysis": WebIntelligenceAgent(),
            "exim_analysis": EXIMAgent(),
            "internal_analysis": InternalKnowledgeAgent(),
        }
        self.report_generator = ReportGeneratorAgent()
        self.progress = {name: "Pending" for name in self.agents}

    def get_analysis_progress(self) -> Dict[str, str]:
        """Returns current status of each agent."""
        return self.progress

    async def _run_agent_async(self, name: str, agent, *args, **kwargs) -> any:
        """Run a single agent asynchronously with timeout and error handling."""
        self.progress[name] = "Running"
        try:
            result = await agent.analyze_async(*args, **kwargs)
            self.progress[name] = "Complete"
            logger.info(f"{name} completed successfully.")
            return result
        except asyncio.TimeoutError:
            self.progress[name] = "Failed"
            logger.error(f"{name} timed out after 30 seconds.")
            return {"error": "Timeout", "confidence": 0.0}
        except Exception as e:
            self.progress[name] = "Failed"
            logger.error(f"{name} failed: {e}")
            return {"error": str(e), "confidence": 0.0}

    def analyze_repurposing(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Synchronous version that works in both sync and async contexts.
        """
        try:
            # Try to get the running loop
            loop = asyncio.get_running_loop()
            # If we get here, we're in an async context
            return loop.run_until_complete(
                self.analyze_repurposing_async(molecule_name, disease_name)
            )
        except RuntimeError:
            # No running event loop, create a new one
            return asyncio.run(self.analyze_repurposing_async(molecule_name, disease_name))
            
    async def analyze_repurposing_async(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Async version - runs all agents in parallel.
        """
        logger.info(f"Starting parallel analysis for {molecule_name} / {disease_name}.")
        
        # Run all agents in parallel
        tasks = [
            self._run_agent_async(name, agent, molecule_name, disease_name)
            for name, agent in self.agents.items()
        ]
        
        # Await all tasks with error handling
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build results dict with error handling
        all_results = {}
        for name, result in zip(self.agents.keys(), results_list):
            if isinstance(result, Exception):
                all_results[name] = {"error": str(result), "confidence": 0.0}
            else:
                all_results[name] = result
                
        all_results["molecule"] = molecule_name
        all_results["disease"] = disease_name
        all_results["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Synthesize results (NOT async - regular call)
        all_results["master_synthesis"] = self.synthesize_results(all_results)

        # Generate PDF report
        pdf_path = await asyncio.to_thread(
            self.report_generator.generate_report, 
            molecule_name, 
            disease_name, 
            all_results
        )
        all_results["pdf_report"] = pdf_path

        logger.info("Parallel analysis complete.")
        return all_results

    def synthesize_results(self, all_agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Regular function - NO async keyword.
        Synthesizes results from all agents.
        """
        weights = {
            "patent_analysis": 0.25,
            "clinical_analysis": 0.20,
            "market_analysis": 0.20,
            "web_analysis": 0.15,
            "exim_analysis": 0.10,
            "internal_analysis": 0.10,
        }
        
        overall_confidence = 0.0
        for agent, weight in weights.items():
            result = all_agent_results.get(agent, {})
            if isinstance(result, dict):
                conf = result.get("confidence", 0.0)
                overall_confidence += float(conf) * weight

        # Determine recommendation
        if overall_confidence >= 0.75:
            recommendation = "PROCEED"
        elif overall_confidence >= 0.5:
            recommendation = "CAUTION"
        else:
            recommendation = "REJECT"

        # Extract key factors
        key_factors = []
        risks = []
        
        patent = all_agent_results.get("patent_analysis", {})
        if isinstance(patent, dict):
            key_factors.append(f"Patent status: {patent.get('patent_status', 'N/A')}")
            if patent.get("fto_status") == "Risk":
                risks.append("Patent infringement risk detected")
        
        clinical = all_agent_results.get("clinical_analysis", {})
        if isinstance(clinical, dict):
            trials = clinical.get("active_trials", 0)
            key_factors.append(f"Active clinical trials: {trials}")
        
        market = all_agent_results.get("market_analysis", {})
        if isinstance(market, dict):
            opp = market.get("opportunity_score", "N/A")
            key_factors.append(f"Market opportunity score: {opp}")

        return {
            "overall_confidence": round(overall_confidence, 2),
            "recommendation": recommendation,
            "key_factors": key_factors,
            "risks": risks if risks else ["No major risks identified"],
            "next_steps": "Proceed to feasibility study" if recommendation == "PROCEED" else "Further analysis required",
        }
