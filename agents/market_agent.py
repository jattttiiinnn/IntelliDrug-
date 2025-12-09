"""
agents/market_agent.py

Analyzes disease market data using Gemini API.
Assesses commercial opportunity based on market size, growth, and competition.
"""

from __future__ import annotations
import os
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from .base_agent import BaseAgent


class MarketAgent(BaseAgent):
    """
    Agent responsible for analyzing the market potential
    for new drugs in a given disease area.
    """

    def __init__(self, data_path: str = "data/market_data.json") -> None:
        """Initialize Gemini client and set data file path."""
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not found in .env file.")
        genai.configure(api_key=api_key)
        self.data_path = data_path

    def analyze(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Analyze market opportunity for a given disease.
        
        Args:
            molecule_name: Name of the molecule (unused in market analysis)
            disease_name: Name of the disease to analyze market for
            
        Returns:
            Dict containing market analysis
            
        Raises:
            ValueError: If disease_name is not provided
        """
        if not disease_name:
            raise ValueError("disease_name is required for market analysis")
            
        return self.analyze_market(disease_name)
        
    async def analyze_async(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Async wrapper for the analyze method.
        
        Args:
            molecule_name: Name of the molecule (unused in market analysis)
            disease_name: Name of the disease to analyze market for
            
        Returns:
            Dict containing market analysis
            
        Raises:
            ValueError: If disease_name is not provided
        """
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.analyze, molecule_name, disease_name)

    def _load_market_data(self) -> list[dict[str, Any]]:
        """Load and parse local market data JSON file."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Market data file not found: {self.data_path}")
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _find_disease_record(self, disease_name: str) -> Dict[str, Any]:
        """Find market data record for a given disease."""
        data = self._load_market_data()
        for entry in data:
            if entry["disease_name"].strip().lower() == disease_name.strip().lower():
                return entry
        raise ValueError(f"Disease '{disease_name}' not found in market_data.json")

    def analyze_market(self, disease_name: str) -> Dict[str, Any]:
        """
        Analyze commercial opportunity for a new drug in the given disease market.

        Returns:
            Dict[str, Any]: {
                "market_size": str,
                "growth_rate": str,
                "competition_level": "Low" | "Medium" | "High",
                "opportunity_score": float (0–10),
                "key_insights": str,
                "confidence": float
            }
        """
        record = self._find_disease_record(disease_name)

        prompt = (
            f"Given this market data: {json.dumps(record)}, "
            f"assess the commercial opportunity for a new drug in {disease_name}. "
            f"Consider market size, growth, and competition. "
            f"Rate opportunity 0-10. "
            f"Return ONLY a JSON object with the following structure:\n"
            f"{{"
            f"  'market_size': str,"
            f"  'growth_rate': str,"
            f"  'competition_level': 'Low' or 'Medium' or 'High',"
            f"  'opportunity_score': float,"
            f"  'key_insights': str,"
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

        # Remove Markdown formatting
        clean_output = re.sub(
            r"^```(?:json)?|```$",
            "",
            raw_output.strip(),
            flags=re.IGNORECASE | re.MULTILINE,
        ).strip()

        # Parse and validate JSON
        try:
            result = json.loads(clean_output)
        except json.JSONDecodeError:
            raise RuntimeError(f"Failed to parse Gemini response as JSON: {raw_output}")

        required_keys = {
            "market_size",
            "growth_rate",
            "competition_level",
            "opportunity_score",
            "key_insights",
            "confidence",
        }
        missing = required_keys - set(result.keys())
        if missing:
            raise RuntimeError(f"Gemini response missing keys: {missing}")

        return result


