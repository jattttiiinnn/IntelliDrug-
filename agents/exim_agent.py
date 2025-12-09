"""
src/agents/exim_agent.py

EXIMAgent: Analyzes pharmaceutical import/export (EXIM) trade data
and assesses sourcing/manufacturing risk using Gemini API.
"""

from __future__ import annotations
import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from .base_agent import BaseAgent


# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class EXIMAgent(BaseAgent):
    """
    Agent to analyze EXIM trade data for a molecule and assess sourcing risk.
    """

    def __init__(self, data_path: Optional[str] = None) -> None:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("❌ GEMINI_API_KEY not found in .env file")

        genai.configure(api_key=api_key)

        # Resolve default data path
        if data_path:
            self.data_path = data_path
        else:
            base = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))
            self.data_path = os.path.join(base, "exim_trade_data.json")

        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"EXIM trade data not found: {self.data_path}")



    def analyze(self, molecule_name: str, disease_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze sourcing/manufacturing risk for the given molecule.
        
        Args:
            molecule_name: Name of the molecule to analyze
            disease_name: Optional disease name (unused in EXIM analysis)
            
        Returns:
            Dict containing sourcing risk analysis
        """
        return self.analyze_sourcing(molecule_name)
        
    async def analyze_async(self, molecule_name: str, disease_name: str = None) -> Dict[str, Any]:
        """
        Async wrapper for the analyze method.
        
        Args:
            molecule_name: Name of the molecule to analyze
            disease_name: Optional disease name (unused in EXIM analysis)
            
        Returns:
            Dict containing sourcing risk analysis
        """
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.analyze, molecule_name, disease_name)
    
    # --------------------------
    # Utility Methods
    # --------------------------

    def _load_trade_data(self) -> List[Dict[str, Any]]:
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("molecules", [])

    @staticmethod
    def _clean_model_output(raw_output: str) -> str:
        """Remove Markdown-style ```json fences."""
        if not raw_output:
            return ""
        return re.sub(r"^```(?:json)?|```$", "", raw_output.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()

    def _call_gemini(self, prompt: str, model_name: str = "gemini-2.5-flash") -> str:
        """Call Gemini API and return raw text output."""
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return getattr(response, "text", str(response))
        except Exception as e:
            logger.error("Gemini API call failed: %s", e)
            raise RuntimeError(f"Gemini API request failed: {e}")

    # --------------------------
    # Core Functionality
    # --------------------------

    def analyze_sourcing(self, molecule_name: str) -> Dict[str, Any]:
        """
        Analyze sourcing/manufacturing risk for the given molecule
        using EXIM trade data and Gemini model.
        """
        logger.info("Starting EXIM analysis for molecule: %s", molecule_name)

        molecules = self._load_trade_data()
        entry = next(
            (m for m in molecules if str(m.get("molecule_name", "")).strip().lower() == molecule_name.strip().lower()),
            None,
        )

        if not entry:
            error_msg = f"Molecule '{molecule_name}' not found in {self.data_path}"
            logger.error(error_msg)
            return {"error": error_msg}

        # Gemini prompt
        prompt = (
            f"Analyze this trade data for {molecule_name}: {json.dumps(entry)}\n\n"
            "Assess manufacturing sourcing risk considering:\n"
            "- Import dependency level\n"
            "- Concentration of suppliers (China risk)\n"
            "- Domestic production capacity\n"
            "- Historical volume trends\n\n"
            "Rate sourcing risk and manufacturing viability.\n"
            "Return ONLY a JSON object with the structure:\n"
            "{\n"
            "  'import_dependency': 'Low'|'Medium'|'High',\n"
            "  'domestic_availability': true|false,\n"
            "  'top_import_sources': list[str],\n"
            "  'sourcing_risk': 'Low'|'Medium'|'High',\n"
            "  'manufacturing_viability': 'Favorable'|'Cautionary'|'Risky',\n"
            "  'key_insights': str,\n"
            "  'confidence': float\n"
            "}"
        )

        # Call Gemini
        try:
            raw = self._call_gemini(prompt)
        except RuntimeError as e:
            logger.warning("Falling back to heuristic analysis due to: %s", e)
            return self._fallback_analysis(entry)

        # Clean and parse
        clean_output = self._clean_model_output(raw)
        try:
            result = json.loads(clean_output)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Gemini JSON output, using fallback.")
            return self._fallback_analysis(entry)

        # Validate required fields
        expected_keys = {
            "import_dependency",
            "domestic_availability",
            "top_import_sources",
            "sourcing_risk",
            "manufacturing_viability",
            "key_insights",
            "confidence",
        }
        missing = expected_keys - set(result.keys())
        if missing:
            logger.warning("Missing keys in Gemini output: %s", missing)
            fallback = self._fallback_analysis(entry)
            for k in missing:
                result[k] = fallback.get(k)

        # Type corrections
        result["confidence"] = float(result.get("confidence", 0.5))
        return result

    # --------------------------
    # Fallback Analysis
    # --------------------------

    def _fallback_analysis(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic backup if Gemini fails."""
        import_dep = entry.get("import_dependency", "Medium")
        dom_prod = entry.get("domestic_production", "Medium")
        top_sources = entry.get("india_imports", {}).get("top_sources", [])
        sourcing_risk = entry.get("sourcing_risk", "Medium")

        domestic_availability = str(dom_prod).lower() in ("high", "medium")

        if import_dep == "Low" and dom_prod == "High":
            viability = "Favorable"
            conf = 0.85
        elif import_dep == "High" and dom_prod == "Low":
            viability = "Risky"
            conf = 0.4
        else:
            viability = "Cautionary"
            conf = 0.6

        insights = (
            f"Import dependency: {import_dep}. Domestic production: {dom_prod}. "
            f"Top sources: {', '.join(top_sources)}. Sourcing risk: {sourcing_risk}."
        )

        return {
            "import_dependency": import_dep,
            "domestic_availability": domestic_availability,
            "top_import_sources": top_sources,
            "sourcing_risk": sourcing_risk,
            "manufacturing_viability": viability,
            "key_insights": insights,
            "confidence": conf,
        }


