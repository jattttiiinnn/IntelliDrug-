"""
agents/patent_agent.py

This module defines the PatentAgent class, which uses the Gemini API
to analyze patent data and determine Freedom to Operate (FTO) status
for a given molecule.

Expected JSON structure in data/patent_data.json:
[
  {
    "molecule_name": "Metformin",
    "patent_holder": "PharmaNova Ltd.",
    "expiry_year": 2026
  },
  ...
]
"""

from __future__ import annotations
import os
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

import google.generativeai as genai
from .base_agent import BaseAgent


class PatentAgent(BaseAgent):
    """
    Agent responsible for analyzing patent status and FTO
    (Freedom to Operate) using Gemini API and local patent data.
    """

    def __init__(self, data_path: str = "data/patent_data.json") -> None:
        """
        Initialize the PatentAgent by configuring the Gemini API client
        and storing the path to the local patent data file.

        Args:
            data_path (str): Path to the JSON file containing patent data.
        """
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not found in .env file.")

        genai.configure(api_key=api_key)
        self.data_path = data_path



    def analyze(self, molecule_name: str, disease_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze the patent status for a given molecule.
        
        Args:
            molecule_name: Name of the molecule to analyze
            disease_name: Optional disease name (kept for interface compatibility)
            
        Returns:
            Dict containing patent status and FTO analysis
        """
        return self.search_patent(molecule_name)
        
    async def analyze_async(self, molecule_name: str, disease_name: str = None) -> Dict[str, Any]:
        """
        Async wrapper for the analyze method.
        
        Args:
            molecule_name: Name of the molecule to analyze
            disease_name: Optional disease name
            
        Returns:
            Dict containing patent status and FTO analysis
        """
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.analyze, molecule_name, disease_name)
    
    def _load_patent_data(self) -> list[dict[str, Any]]:
        """Load and parse local patent data JSON file."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Patent data file not found: {self.data_path}")

        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _find_molecule_record(self, molecule_name: str) -> Dict[str, Any]:
        """Return the patent record for the given molecule, or raise ValueError."""
        data = self._load_patent_data()
        for entry in data:
            if entry["molecule_name"].strip().lower() == molecule_name.strip().lower():
                return entry
        raise ValueError(f"Molecule '{molecule_name}' not found in patent_data.json")

    def search_patent(self, molecule_name: str) -> Dict[str, Any]:
        """
        Analyze the patent and FTO status for a given molecule.

        Args:
            molecule_name (str): Name of the molecule to analyze.

        Returns:
            Dict[str, Any]: A structured dictionary containing:
                {
                  "molecule": str,
                  "patent_status": "Active" or "Expired",
                  "expiry_date": str,
                  "fto_status": "Clear" or "Risk",
                  "confidence": float (0–1),
                  "reasoning": str
                }

        Raises:
            ValueError: If molecule is not found.
            RuntimeError: If Gemini API call or response parsing fails.
        """
        molecule_record = self._find_molecule_record(molecule_name)

        prompt = (
            f"You are a patent analyst. "
            f"Given this patent data: {json.dumps(molecule_record)}, "
            f"analyze the patent status for {molecule_name} and determine Freedom to Operate status. "
            f"Return ONLY a JSON object with the structure:\n"
            f"{{"
            f"  'molecule': str,"
            f"  'patent_status': 'Active' or 'Expired',"
            f"  'expiry_date': str,"
            f"  'fto_status': 'Clear' or 'Risk',"
            f"  'confidence': float (0-1),"
            f"  'reasoning': str"
            f"}}"
        )

        try:
            response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
        except Exception as e:
            raise RuntimeError(f"Gemini API request failed: {e}")

        if not response or not hasattr(response, "text"):
            raise RuntimeError("Gemini API returned an empty response.")

        raw_output = response.text.strip()

        # Try to parse the JSON part of the model's output
        try:
            # Strip Markdown code fences like ```json ... ```
            clean_output = re.sub(
                r"^```(?:json)?|```$",
                "",
                raw_output.strip(),
                flags=re.IGNORECASE | re.MULTILINE,
            ).strip()

            result = json.loads(clean_output)
        except json.JSONDecodeError:
            raise RuntimeError(f"Failed to parse Gemini response as JSON: {raw_output}")
        # Validate structure
        required_keys = {
            "molecule",
            "patent_status",
            "expiry_date",
            "fto_status",
            "confidence",
            "reasoning",
        }
        missing = required_keys - set(result.keys())
        if missing:
            raise RuntimeError(f"Gemini response missing keys: {missing}")

        return result
