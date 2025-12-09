"""
agents/clinical_trials_agent.py

Analyzes clinical trial data for a given molecule and disease using Gemini API.
Summarizes active trial counts, phase distribution, and sponsor insights.
"""

from __future__ import annotations
import os
import json
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from .base_agent import BaseAgent


class ClinicalTrialsAgent(BaseAgent):
    """
    Agent responsible for analyzing clinical trial activity for a molecule-disease pair.
    """

    def __init__(self, data_path: str = "data/clinical_trials.json") -> None:
        """
        Initialize Gemini client and set data file path.
        """
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not found in .env file.")
        genai.configure(api_key=api_key)
        self.data_path = data_path

    def analyze(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Analyze clinical trial landscape for the given molecule and disease.

        Args:
            molecule_name: Name of the molecule to analyze
            disease_name: Disease name (required for clinical trials)

        Returns:
            Dict containing clinical trial analysis
            
        Raises:
            ValueError: If disease_name is not provided
        """
        if not disease_name:
            raise ValueError("disease_name is required for clinical trials analysis")
            
        return self.search_trials(molecule_name, disease_name)
        
    async def analyze_async(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Async wrapper for the analyze method.
        
        Args:
            molecule_name: Name of the molecule to analyze
            disease_name: Disease name (required for clinical trials)
            
        Returns:
            Dict containing clinical trial analysis
            
        Raises:
            ValueError: If disease_name is not provided
        """
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.analyze, molecule_name, disease_name)

    def _load_trials_data(self) -> list[dict[str, Any]]:
        """Load and parse local clinical trials JSON file."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Clinical trials data not found: {self.data_path}")
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _filter_trials(self, molecule_name: str, disease_name: str) -> list[dict[str, Any]]:
        """Filter trials matching molecule and disease."""
        trials = self._load_trials_data()
        matches = [
            t for t in trials
            if t["molecule_name"].strip().lower() == molecule_name.strip().lower()
            and t["disease"].strip().lower() == disease_name.strip().lower()
        ]
        if not matches:
            raise ValueError(f"No trials found for molecule '{molecule_name}' and disease '{disease_name}'.")
        return matches

    def search_trials(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Analyze clinical trial landscape for the given molecule and disease.

        Returns:
            Dict[str, Any]: {
                "active_trials": int,
                "phases": {"phase_1": int, "phase_2": int, "phase_3": int},
                "key_sponsors": list[str],
                "latest_findings": str,
                "confidence": float
            }
        """
        trials = self._filter_trials(molecule_name, disease_name)
        prompt = (
            f"Analyze these clinical trials: {json.dumps(trials)}. "
            f"Summarize the trial landscape for {molecule_name} in {disease_name}. "
            f"Focus on phase distribution and sponsor credibility. "
            f"Return ONLY a JSON object with this structure:\n"
            f"{{"
            f"  'active_trials': int,"
            f"  'phases': {{'phase_1': int, 'phase_2': int, 'phase_3': int}},"
            f"  'key_sponsors': list[str],"
            f"  'latest_findings': str,"
            f"  'confidence': float"
            f"}}"
        )

        try:
            response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
        except Exception as e:
            raise RuntimeError(f"Gemini API request failed: {e}")

        if not response or not hasattr(response, "text"):
            raise RuntimeError("Gemini API returned an empty response.")

        raw_output = response.text.strip()

        # Clean Markdown formatting
        clean_output = re.sub(
            r"^```(?:json)?|```$",
            "",
            raw_output.strip(),
            flags=re.IGNORECASE | re.MULTILINE,
        ).strip()

        # Parse JSON
        try:
            result = json.loads(clean_output)
        except json.JSONDecodeError:
            raise RuntimeError(f"Failed to parse Gemini response as JSON: {raw_output}")

        # Validate structure
        required_keys = {"active_trials", "phases", "key_sponsors", "latest_findings", "confidence"}
        missing = required_keys - set(result.keys())
        if missing:
            raise RuntimeError(f"Gemini response missing keys: {missing}")

        return result



