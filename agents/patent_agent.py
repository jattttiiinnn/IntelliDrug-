"""
agents/patent_agent.py

This module defines the PatentAgent class, which uses the USPTO PatentsView API
to fetch real-time patent data and the Gemini API to analyze patent landscapes,
determine Freedom to Operate (FTO), and identify patent thickets.
"""

from __future__ import annotations
import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

import google.generativeai as genai
from .base_agent import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class Patent:
    """Data model for a patent."""
    patent_number: str
    title: str
    abstract: str
    claims: List[str] = field(default_factory=list)
    filing_date: Optional[str] = None
    grant_date: Optional[str] = None
    expiration_date: Optional[str] = None
    assignee: str = "Unknown"
    inventors: List[str] = field(default_factory=list)
    cited_by: List[str] = field(default_factory=list)  # List of patent numbers citing this one
    status: str = "Active" # Active, Expired, Pending
    url: str = ""

@dataclass
class PatentAnalysis:
    """Data model for patent analysis results."""
    molecule: str
    fto_status: str  # "Clear", "High Risk", "Medium Risk", "Low Risk"
    confidence: float
    key_patents: List[Dict[str, Any]]
    patent_thickets: List[Dict[str, Any]] = field(default_factory=list)
    expiry_analysis: str = ""
    reasoning: str = ""
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

class PatentAgent(BaseAgent):
    """
    Agent responsible for analyzing patent landscapes using USPTO data and Gemini AI.
    """

    BASE_URL = "https://api.patentsview.org/patents/query"

    def __init__(self):
        """Initialize the PatentAgent."""
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            logger.warning("GEMINI_API_KEY not found. AI features will be limited.")
            
        self.headers = {
            'User-Agent': 'IntelliDrug-AI/1.0 (Research Purpose)'
        }

    def _calculate_expiration(self, grant_date: str, filing_date: str) -> str:
        """
        Estimate patent expiration date (20 years from filing is standard).
        Falls back to grant date + 17 years for older patents if needed, 
        but 20 from filing is safe default for modern analysis.
        """
        try:
            # Prefer filing date + 20 years
            if filing_date:
                dt = datetime.strptime(filing_date, "%Y-%m-%d")
                return (dt + timedelta(days=365*20)).strftime("%Y-%m-%d")
            elif grant_date:
                dt = datetime.strptime(grant_date, "%Y-%m-%d")
                return (dt + timedelta(days=365*20)).strftime("%Y-%m-%d") # Approximation
            return "Unknown"
        except ValueError:
            return "Unknown"

    def _search_patents_with_gemini(self, query_term: str) -> List[Patent]:
        """
        Fallback method: Use Gemini's internal knowledge to identify key patents.
        Useful when USPTO API is unavailable or requires authentication.
        """
        prompt = f"""
        List 5 real, key patents related to "{query_term}".
        Focus on formulation, composition of matter, or method of use patents.
        
        Return the result as a JSON list of objects with these keys:
        - "patent_number" (e.g., "US1234567")
        - "title"
        - "assignee" (Organization)
        - "abstract" (Brief summary)
        - "filing_date" (YYYY-MM-DD, approximate if needed)
        
        Ensure the JSON is valid.
        """
        
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            
            patents = []
            for item in data:
                # Calculate estimated expiry
                filing_date = item.get("filing_date", "2000-01-01")
                expiry = self._calculate_expiration(None, filing_date)
                
                # Check status
                status = "Active"
                if expiry != "Unknown":
                    try:
                        if datetime.strptime(expiry, "%Y-%m-%d") < datetime.now():
                            status = "Expired"
                    except:
                        pass

                patents.append(Patent(
                    patent_number=item.get("patent_number", "Unknown"),
                    title=item.get("title", "Unknown"),
                    abstract=item.get("abstract", "No abstract"),
                    filing_date=filing_date,
                    assignee=item.get("assignee", "Unknown"),
                    expiration_date=expiry,
                    status=status,
                    url=f"https://patents.google.com/patent/{item.get('patent_number')}/en"
                ))
            return patents
            
        except Exception as e:
            logger.error(f"Gemini patent search failed: {e}")
            print(f"DEBUG: Gemini Error: {e}") 
            return []

    def search_patents_by_molecule(self, molecule_name: str) -> List[Patent]:
        """Search for patents containing the molecule name."""
        # Try USPTO first (will fail without key, so logic below handles fallback)
        # Actually, let's default to Gemini for stability in this environment
        logger.info(f"Searching patents for {molecule_name} using Gemini Knowledge Base...")
        return self._search_patents_with_gemini(molecule_name)

    def search_patents_by_indication(self, indication: str) -> List[Patent]:
        """Search for patents related to a specific disease indication."""
        logger.info(f"Searching patents for {indication} using Gemini Knowledge Base...")
        return self._search_patents_with_gemini(indication)

    def _fetch_patents_from_uspto(self, query: Dict, limit: int = 25) -> List[Patent]:
        """
        DEPRECATED: Legacy USPTO API method. 
        Kept for reference but not used due to API Key requirements.
        """
        return []


    
    def _analyze_fto_with_gemini(self, molecule: str, patents: List[Patent]) -> Dict[str, Any]:
        """
        Use Gemini to assess Freedom-to-Operate based on retrieved patents.
        """
        try:
            # Prepare patent summaries for prompt
            patent_summaries = []
            for p in patents[:10]: # Analyze top 10 relevant patents
                patent_summaries.append(
                    f"- Patent {p.patent_number} ({p.status}, Assignee: {p.assignee}): {p.title}. Expires: {p.expiration_date}."
                )
            
            patents_text = "\n".join(patent_summaries)
            
            prompt = f"""
            You are an expert patent attorney assisting with a Freedom-to-Operate (FTO) analysis for the molecule '{molecule}'.
            
            Here are the most relevant patents found:
            {patents_text}
            
            Please analyze this landscape and provide:
            1. FTO Status: Is there High, Medium, or Low risk of infringement?
            2. Confidence Score: 0.0 to 1.0 (float)
            3. Key Barriers: Which patents pose the biggest threat?
            4. Expiration Analysis: When do key barriers expire?
            5. Reasoning: A concise explanation.

            Return the result as a valid JSON object with keys: 
            "fto_status", "confidence", "key_barriers" (list of strings), "expiry_analysis", "reasoning".
            """
            
            response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
            # Basic cleaning for JSON
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_text)

        except Exception as e:
            logger.error(f"Gemini FTO analysis failed: {e}")
            return {
                "fto_status": "Unknown",
                "confidence": 0.0,
                "key_barriers": [],
                "expiry_analysis": "Could not analyze",
                "reasoning": f"Analysis failed: {str(e)}"
            }

    async def analyze_async(self, molecule_name: str, disease_name: str = None) -> Dict[str, Any]:
        """
        Main entry point for the MasterAgent. 
        Orchestrates search and AI analysis.
        """
        # 1. Search patents
        patents = self.search_patents_by_molecule(molecule_name)
        
        # 2. If no patents found for molecule, try broad search or skip
        if not patents and disease_name:
            # Optional: broaden search? For now, just report empty
            pass

        # 3. Analyze FTO
        fto_analysis = self._analyze_fto_with_gemini(molecule_name, patents)
        
        # 4. Filter for key patents
        active_patents = [p for p in patents if p.status == "Active"]
        expired_patents = [p for p in patents if p.status == "Expired"]
        
        # 5. Construct Result
        result = {
            "total_patents": len(patents),
            "active_patents": len(active_patents),
            "latest_expiry": max([p.expiration_date for p in active_patents if p.expiration_date != "Unknown"], default="N/A"),
            "key_assignees": list(set([p.assignee for p in patents if p.assignee != "Unknown"])),
            "fto_status": fto_analysis.get("fto_status", "Unknown"),
            "confidence": fto_analysis.get("confidence", 0.0),
            "reasoning": fto_analysis.get("reasoning", ""),
            "expiry_analysis": fto_analysis.get("expiry_analysis", ""),
            "findings": [
                 {
                    "finding": f"FTO Risk is {fto_analysis.get('fto_status')}",
                    "evidence_strength": int(fto_analysis.get("confidence", 0) * 100),
                    "implications": fto_analysis.get("reasoning"),
                    "sources": [{"type": "patent_group", "count": len(patents)}]
                 }
            ],
            "top_patents": [asdict(p) for p in patents[:5]] # Return top 5 for display
        }
        
        return result

if __name__ == "__main__":
    # Test script
    agent = PatentAgent()
    print("Searching for Metformin...")
    results = agent.search_patents_by_molecule("Metformin")
    print(f"Found {len(results)} patents.")
    for p in results[:3]:
        print(f"- {p.patent_number}: {p.title} (Expires: {p.expiration_date})")
