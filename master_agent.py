# master_agent.py
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import asyncio
import logging
import json
import os

# Worker agents
from agents.patent_agent import PatentAgent
from agents.clinical_trials_agent import ClinicalTrialsAgent
from agents.market_agent import MarketAgent
from agents.web_intelligence_agent import WebIntelligenceAgent
from agents.exim_agent import EXIMAgent
from agents.internal_knowledge_agent import InternalKnowledgeAgent
from agents.report_generator_agent import ReportGeneratorAgent
from conversation_manager import ConversationManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class AnalysisStrategy(Enum):
    STANDARD = "standard"
    OPTIMISTIC = "optimistic"
    CONSERVATIVE = "conservative"

class MasterAgent:
    """
    Orchestrates all analysis agents in parallel using asyncio.
    """

    def __init__(self):
        if os.environ.get("MOCK_AGENTS") == "1":
            from unittest.mock import AsyncMock
            logger.info("TEST MODE: Using mocked agents.")
            self.agents = {
                "patent_analysis": AsyncMock(),
                "clinical_analysis": AsyncMock(),
                "market_analysis": AsyncMock(),
                "web_analysis": AsyncMock(),
                "exim_analysis": AsyncMock(),
                "internal_analysis": AsyncMock(),
            }
            # Configure mock returns
            mock_result = {
                "confidence": 0.9,
                "findings": [{"finding": "Mocked finding", "evidence_strength": 90, "is_positive": True}],
                "active_trials": 10,
                "patent_status": "Active",
                "opportunity_score": 85,
            }
            for agent in self.agents.values():
                agent.analyze_async.return_value = mock_result
            
            # Mock report generator specifically
            self.report_generator = AsyncMock()
            self.report_generator.generate_report.return_value = "mock_report.pdf"
        else:
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
        self.conversation_manager = ConversationManager()
        
        # Map agent names to their display names
        self.agent_display_names = {
            "patent_analysis": "Patent Analysis",
            "clinical_analysis": "Clinical Trials",
            "market_analysis": "Market Analysis",
            "web_analysis": "Web Intelligence",
            "exim_analysis": "EXIM Analysis",
            "internal_analysis": "Internal Knowledge"
        }

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
        all_results["synthesis"] = self.synthesize_results(all_results)

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

    async def compare_molecules_async(self, molecules: List[str], disease_name: str) -> Dict[str, Any]:
        """
        Compare multiple molecules for a given disease.
        Runs analysis for each molecule in parallel and returns combined results.
        """
        if len(molecules) < 2:
            raise ValueError("At least 2 molecules are required for comparison")
            
        logger.info(f"Starting comparison of {len(molecules)} molecules for {disease_name}")
        
        # Run analysis for each molecule in parallel
        tasks = [
            self.analyze_repurposing_async(mol, disease_name)
            for mol in molecules
        ]
        
        # Gather all results
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        comparison_results = {}
        for mol, result in zip(molecules, results_list):
            if isinstance(result, Exception):
                comparison_results[mol] = {
                    "error": str(result),
                    "molecule": mol,
                    "disease": disease_name
                }
            else:
                comparison_results[mol] = result
        
        # Add comparison metadata
        comparison_results["comparison_metadata"] = {
            "disease": disease_name,
            "molecules": molecules,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Generate comparison synthesis
        comparison_results["comparison_synthesis"] = await asyncio.to_thread(
            self.synthesize_comparison, comparison_results
        )
        
        # Store the comparison results in the conversation context
        for mol, result in comparison_results.items():
            if isinstance(result, dict) and 'synthesis' in result:
                for agent_name, agent_result in result.items():
                    if agent_name in self.agents:
                        context_key = f"{mol}_{agent_name}"
                        self.conversation_manager.agent_contexts[context_key] = agent_result
                        
        return comparison_results
        
    def synthesize_results(self, all_agent_results: Dict[str, Any], strategy: AnalysisStrategy = AnalysisStrategy.STANDARD) -> Dict[str, Any]:
        """
        Synthesizes results from all agents for a single molecule.

        - Handles comparison results (comparison_metadata).
        - Computes weighted overall_confidence from agent-level confidences.
        - Optionally uses per-finding evidence_strength / is_positive from agents.
        """
        # 1. Comparison mode shortcut
        if "comparison_metadata" in all_agent_results:
            return self.synthesize_comparison(all_agent_results)

        # 2. Base agent-level weighting and confidence calculation
        # 2. Base agent-level weighting and confidence calculation
        weights = self.get_weights(strategy)

        # Collect individual agent confidences for uncertainty calculation
        agent_confidences = []
        weighted_confidences = []
        
        for agent, weight in weights.items():
            result = all_agent_results.get(agent, {})
            if isinstance(result, dict):
                try:
                    conf = float(result.get("confidence", 0.0))
                    agent_confidences.append(conf)
                    weighted_confidences.append(conf * weight)
                except (TypeError, ValueError):
                    # Default to 0 confidence if invalid
                    agent_confidences.append(0.0)
                    weighted_confidences.append(0.0)
        
        # Calculate overall confidence (weighted average)
        overall_confidence = sum(weighted_confidences)
        
        # Calculate standard deviation of agent confidences
        if len(agent_confidences) > 1:
            import math
            mean_confidence = sum(agent_confidences) / len(agent_confidences)
            variance = sum((x - mean_confidence) ** 2 for x in agent_confidences) / len(agent_confidences)
            uncertainty = math.sqrt(variance)
            uncertainty_pct = min(100, max(0, int(uncertainty * 100)))  # Convert to percentage (0-100)
        else:
            uncertainty_pct = 0  # Default to 0 if not enough data

        # 3. Evidence-based weighting from findings (new logic)
        evidence_total_weight = 0.0
        evidence_weighted_score = 0.0
        evidence_findings: List[Dict[str, Any]] = []

        strengths: List[str] = []
        weaknesses: List[str] = []
        key_factors: List[str] = []
        risks: List[str] = []

        # --- Patent analysis (original key factors/risks) ---
        patent = all_agent_results.get("patent_analysis", {})
        if isinstance(patent, dict):
            status = patent.get("patent_status", "N/A")
            key_factors.append(f"Patent status: {status}")
            if isinstance(status, str):
                if status.lower() == "active":
                    strengths.append("Active patent protection")
                elif status.lower() == "expired":
                    weaknesses.append("Patent expired")

            if patent.get("fto_status") == "Risk":
                risks.append("Patent infringement risk detected")

        # --- Clinical analysis ---
        clinical = all_agent_results.get("clinical_analysis", {})
        if isinstance(clinical, dict):
            trials = clinical.get("active_trials", 0)
            key_factors.append(f"Active clinical trials: {trials}")
            try:
                if int(trials) > 0:
                    strengths.append(f"Active in {trials} clinical trials")
                else:
                    weaknesses.append("No active clinical trials found")
            except (TypeError, ValueError):
                pass

        # --- Market analysis ---
        market = all_agent_results.get("market_analysis", {})
        if isinstance(market, dict):
            opp = market.get("opportunity_score", "N/A")
            key_factors.append(f"Market opportunity score: {opp}")

        # --- New: process agent-level findings if present ---
        for agent_name, result in all_agent_results.items():
            if not isinstance(result, dict):
                continue
            findings = result.get("findings")
            if not isinstance(findings, list):
                continue

            for finding in findings:
                if not isinstance(finding, dict):
                    continue

                # Normalize evidence strength 0–100 -> 0–1
                strength_val = finding.get("evidence_strength", 50)
                try:
                    strength_norm = float(strength_val) / 100.0
                except (TypeError, ValueError):
                    strength_norm = 0.5  # default

                evidence_weighted_score += strength_norm
                evidence_total_weight += 1.0

                record = {
                    "finding": finding,
                    "weight": strength_norm,
                    "agent": agent_name,
                }
                evidence_findings.append(record)

                # Categorize positive / negative
                is_positive = finding.get("is_positive", True)
                text = finding.get("finding") or finding.get("description")
                if isinstance(text, str):
                    if is_positive:
                        strengths.append(text)
                    else:
                        weaknesses.append(text)

        # Evidence-based score (0–100)
        if evidence_total_weight > 0:
            evidence_based_score = int((evidence_weighted_score / evidence_total_weight) * 100)
        else:
            evidence_based_score = int(overall_confidence * 100)

        # 4. Overall recommendation with uncertainty
        if overall_confidence >= 0.75:
            recommendation = "PROCEED"
            confidence_label = "High"
        elif overall_confidence >= 0.5:
            recommendation = "PROCEED WITH CAUTION"
            confidence_label = "Medium"
        elif overall_confidence >= 0.4:
            recommendation = "REVIEW REQUIRED"
            confidence_label = "Low"
        else:
            recommendation = "NOT RECOMMENDED"
            confidence_label = "Very Low"
            
        # Add NEEDS REVIEW flag if confidence is low
        needs_review = overall_confidence < 0.6
        if needs_review:
            recommendation += " (NEEDS REVIEW)"

        # 5. Final numeric score (0–100) from overall_confidence
        score = int(overall_confidence * 100)
        confidence_pct = int(overall_confidence * 100)

        # 6. Build summary
        molecule = all_agent_results.get("molecule", "the molecule")
        disease = all_agent_results.get("disease", "the target disease")

        summary_parts = [
            f"Analysis of {molecule} for {disease} suggests to {recommendation.lower()}",
            f"with {int(overall_confidence * 100)}% confidence.",
        ]
        if key_factors:
            summary_parts.append(f"Key factors include: {', '.join(key_factors[:3])}.")
        summary_parts.append(f"Evidence-based score: {evidence_based_score}/100.")

        summary = " ".join(summary_parts)

        # 7. Top 3 key factors from findings by evidence strength
        if evidence_findings:
            top_findings = sorted(
                evidence_findings,
                key=lambda x: x["weight"],
                reverse=True,
            )[:3]
            # Extend key_factors with these, but avoid duplicates
            for f in top_findings:
                text = f["finding"].get("finding") or f["finding"].get("description")
                if isinstance(text, str) and text not in key_factors:
                    key_factors.append(text)

        # Format confidence display with uncertainty
        confidence_display = f"{confidence_pct}% ±{uncertainty_pct}%"
        
        # Add confidence tooltip
        confidence_tooltip = (
            "Confidence is based on agreement between analysis agents. "
            f"Low confidence ({confidence_pct}% ±{uncertainty_pct}%) suggests more research is needed."
        )
        
        # Prepare agent confidence data for visualization
        agent_confidence_data = []
        for agent, conf in zip(weights.keys(), agent_confidences):
            agent_confidence_data.append({
                "agent": self.agent_display_names.get(agent, agent),
                "confidence": int(conf * 100),
                "weight": weights[agent]
            })
        
        return {
            "recommendation": recommendation,
            "confidence": round(overall_confidence, 4),  # numeric (0-1)
            "confidence_display": confidence_display,    # Formatted string "X% ±Y%"
            "confidence_interval": uncertainty_pct,      # ± value in percentage
            "confidence_label": confidence_label,        # string label (High/Medium/Low)
            "confidence_tooltip": confidence_tooltip,    # Help text about confidence
            "agent_confidences": agent_confidence_data,  # Individual agent confidences
            "score": score,                              # 0–100 from overall_confidence
            "evidence_based_score": evidence_based_score, # 0–100 from findings
            "key_factors": key_factors,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "risks": risks if risks else ["No significant risks identified"],
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "needs_review": needs_review,                # Boolean flag for low confidence
        }
        
    def get_conversation_history(self, molecule: str, disease: str) -> List[Dict]:
        """Get the conversation history for a specific analysis."""
        return self.conversation_manager.get_conversation(molecule, disease)
        
    def synthesize_comparison(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize comparison results from multiple molecule analyses.
        """
        molecules = comparison_results.get("comparison_metadata", {}).get("molecules", [])
        if not molecules:
            return {"error": "No molecules to compare"}
            
        # Extract synthesis for each molecule
        molecule_data = {}
        for mol in molecules:
            if mol in comparison_results and "synthesis" in comparison_results[mol]:
                molecule_data[mol] = comparison_results[mol]["synthesis"]
        
        if not molecule_data:
            return {"error": "No valid molecule data to compare"}
            
        # Generate comparison summary
        best_mol = max(
            molecule_data.items(),
            key=lambda x: x[1].get("score", 0),
            default=(None, None)
        )
        
        if best_mol[0] is None:
            return {"error": "Could not determine best candidate"}
            
        best_score = best_mol[1].get("score", 0)
        best_molecules = [
            mol for mol, data in molecule_data.items()
            if data.get("score", 0) == best_score
        ]
        
        # Generate comparison points
        comparison_points = []
        for mol, data in molecule_data.items():
            comparison_points.append({
                "molecule": mol,
                "score": data.get("score", 0),
                "recommendation": data.get("recommendation", "UNKNOWN"),
                "confidence": data.get("confidence", 0),
                "strengths": data.get("strengths", []),
                "weaknesses": data.get("weaknesses", []),
                "risks": data.get("risks", [])
            })
        
        # Sort by score (descending)
        comparison_points.sort(key=lambda x: x["score"], reverse=True)
        
        # Generate summary
        if len(best_molecules) == 1:
            summary = (
                f"{best_molecules[0]} is the top candidate with a score of {best_score}/100. "
                f"Key strengths: {', '.join(molecule_data[best_molecules[0]].get('strengths', ['None'])[:2])}."
            )
        else:
            summary = (
                f"{len(best_molecules)} molecules tied with top score of {best_score}/100: "
                f"{', '.join(best_molecules)}."
            )
        
        return {
            "summary": summary,
            "best_candidates": best_molecules,
            "top_score": best_score,
            "comparison": comparison_points,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    def calculate_evidence_strength(self, sources: List[Dict]) -> int:
        """
        Calculate evidence strength score (0-100) based on multiple criteria.
        
        Args:
            sources: List of source dictionaries with 'type', 'year', and 'reliability' keys
            
        Returns:
            int: Evidence strength score (0-100)
        """
        if not sources:
            return 0
            
        # Calculate source credibility (0-1)
        source_scores = {
            'pubmed': 1.0,
            'clinical_trials': 0.9,
            'patent': 0.8,
            'regulatory': 0.9,
            'market_report': 0.7,
            'news': 0.5,
            'blog': 0.3
        }
        
        # Calculate average source credibility
        credibility = sum(
            source_scores.get(src.get('type', '').lower(), 0.3) 
            for src in sources
        ) / len(sources)
        
        # Calculate recency (0-1, more recent = higher)
        current_year = datetime.now().year
        recency = sum(
            max(0, 1 - (current_year - int(src.get('year', current_year))) * 0.1)
            for src in sources
        ) / len(sources)
        
        # Normalize source count (0-1, more sources = higher, capped at 10)
        source_count = min(1.0, len(sources) / 10)
        
        # Calculate consensus (0-1, higher if sources agree)
        # This is a simplified version - you might want to implement more sophisticated logic
        consensus = 0.7  # Placeholder - implement based on your data
        
        # Calculate weighted score
        score = (
            self.evidence_weights['source_credibility'] * credibility +
            self.evidence_weights['recency'] * recency +
            self.evidence_weights['source_count'] * source_count +
            self.evidence_weights['consensus'] * consensus
        )
        
        return int(score * 100)
    
    def get_evidence_badge(self, score: int) -> str:
        """Return HTML for a color-coded evidence badge."""
        if score >= 80:
            color = "success"
            label = "Strong Evidence"
        elif score >= 50:
            color = "warning"
            label = "Moderate Evidence"
        else:
            color = "danger"
            label = "Weak Evidence"
            
        return f"""
        <span class="badge bg-{color}" style="font-size: 0.8em; padding: 0.25em 0.6em; border-radius: 0.25rem;">
            {label}: {score}/100
        </span>
        """

    def get_weights(self, strategy: AnalysisStrategy = AnalysisStrategy.STANDARD) -> Dict[str, float]:
        """Get agent weights based on analysis strategy."""
        base_weights = {
            "patent_analysis": 0.25,
            "clinical_analysis": 0.20,
            "market_analysis": 0.20,
            "web_analysis": 0.15,
            "exim_analysis": 0.10,
            "internal_analysis": 0.10,
        }
        
        if strategy == AnalysisStrategy.OPTIMISTIC:
            # Increase weight for positive indicators
            return {
                **base_weights,
                "clinical_analysis": 0.25,  # Higher weight for clinical data
                "market_analysis": 0.25,    # Higher weight for market potential
                "web_analysis": 0.20,       # Higher weight for web intelligence
            }
        elif strategy == AnalysisStrategy.CONSERVATIVE:
            # Increase weight for risk indicators
            return {
                **base_weights,
                "patent_analysis": 0.30,    # Higher weight for patent risks
                "market_analysis": 0.15,    # Lower weight for market potential
                "internal_analysis": 0.15,  # Higher weight for internal knowledge
            }
        return base_weights



    async def analyze_with_strategy(self, molecule_name: str, disease_name: str, strategy: AnalysisStrategy) -> Dict[str, Any]:
        """Run analysis with a specific strategy."""
        results = await self.analyze_repurposing_async(molecule_name, disease_name)
        synthesis = self.synthesize_results(results, strategy)
        results["synthesis"] = synthesis
        results["analysis_strategy"] = strategy.value
        return results
