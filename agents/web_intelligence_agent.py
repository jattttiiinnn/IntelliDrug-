"""
src/agents/web_intelligence_agent.py

WebIntelligenceAgent

- search_literature(molecule_name, disease_name)
    * searches data/pubmed_articles.json
    * returns top 5 most relevant articles and a short Gemini summary of key findings

- get_guidelines(disease_name)
    * returns guideline-type "articles" for the disease

- analyze(molecule_name, disease_name)
    * combines literature + guidelines and uses Gemini to synthesize final insights

This module follows the pattern used in your other agents:
- loads GEMINI_API_KEY from .env
- configures google.generativeai
- uses regex to strip Markdown fences from model output
- validates returned JSON structure
"""

from __future__ import annotations
import os
import json
import re
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from .base_agent import BaseAgent

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class WebIntelligenceAgent(BaseAgent):
    """
    Agent for searching and synthesizing medical literature from a local pubmed-style JSON file.
    """

    def __init__(self, data_path: Optional[str] = None) -> None:
        """
        Initialize the agent and configure Gemini API.

        Args:
            data_path: Optional path to pubmed_articles.json. If None, defaults to project/data/pubmed_articles.json
        """
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not found in environment (.env).")
        genai.configure(api_key=api_key)

        # Resolve default data path relative to this file
        if data_path:
            self.data_path = data_path
        else:
            # src/agents -> go up two levels to project root, then data/
            # base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
            # self.data_path = os.path.join(base, "pubmed_articles.json")
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
            self.data_path = os.path.join(base, "pubmed_articles.json")


        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"PubMed articles JSON not found at: {self.data_path}")

    async def analyze_async(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Async wrapper for the analyze method.
        
        Args:
            molecule_name: Name of the molecule to analyze
            disease_name: Disease name to analyze
            
        Returns:
            Dict containing literature and guidelines analysis
        """
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.analyze, molecule_name, disease_name)

    # -------------------------
    # Helper: load articles file
    # -------------------------
    def _load_articles(self) -> List[Dict[str, Any]]:
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        articles = data.get("articles", [])
        return articles

    # -------------------------
    # Helper: clean model output
    # -------------------------
    @staticmethod
    def _clean_model_output(raw_output: str) -> str:
        """
        Remove markdown fences like ```json ... ``` and return the inner text.
        """
        if not raw_output:
            return ""
        clean = re.sub(r"^```(?:json)?|```$", "", raw_output.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()
        return clean

    # -------------------------
    # Helper: call Gemini with retries/validation
    # -------------------------
    def _call_gemini(self, prompt: str, model_name: str = "gemini-2.5-flash") -> str:
        """
        Call the configured Gemini model with the prompt and return the raw text output.

        Raises RuntimeError on API failures.
        """
        try:
            # Use same pattern as other agents
            response = genai.GenerativeModel(model_name).generate_content(prompt)
        except Exception as e:
            logger.error("Gemini API call failed: %s", e)
            raise RuntimeError(f"Gemini API request failed: {e}")

        # Different SDK/versions may return different shapes; prefer .text if present
        if not response:
            raise RuntimeError("Gemini returned empty response.")

        # Many versions expose response.text; fallback to string representation
        raw_text = getattr(response, "text", None)
        if raw_text is None:
            # try candidates or content parts (best-effort)
            try:
                # some SDKs: response.candidates[0].content[0].text or similar — try to be flexible
                raw_text = str(response)
            except Exception:
                raw_text = ""

        return raw_text

    # -------------------------
    # Method: search_literature
    # -------------------------
    def search_literature(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Search the local pubmed-like JSON for articles matching molecule and disease,
        return top 5 by relevance_score, and ask Gemini to summarize key findings.

        Returns:
            {
              "articles": [ ... top 5 article dicts ... ],
              "summary": "short summary text generated by Gemini"
            }
        """
        logger.info("Searching literature for molecule=%s, disease=%s", molecule_name, disease_name)
        articles = self._load_articles()

        # Filter by molecule and disease (case-insensitive). Support comma-separated molecule fields.
        def matches(a: Dict[str, Any]) -> bool:
            mol_field = str(a.get("molecule", "")).lower()
            dis_field = str(a.get("disease", "")).lower()
            # molecule match: either exact or included in comma-separated list
            mol_match = molecule_name.strip().lower() in [m.strip() for m in mol_field.split(",")]
            dis_match = disease_name.strip().lower() == dis_field
            return mol_match and dis_match

        filtered = [a for a in articles if matches(a)]

        if not filtered:
            logger.info("No literature found for %s in %s", molecule_name, disease_name)
            return {"articles": [], "summary": ""}

        # Sort by relevance_score (desc) and take top 5
        def rel_score(a: Dict[str, Any]) -> float:
            try:
                return float(a.get("relevance_score", 0.0))
            except Exception:
                return 0.0

        filtered_sorted = sorted(filtered, key=rel_score, reverse=True)
        top5 = filtered_sorted[:5]

        # Prepare a concise representation for the model (avoid huge dumps)
        articles_for_prompt = [
            {
                "pmid": a.get("pmid"),
                "title": a.get("title"),
                "year": a.get("year"),
                "journal": a.get("journal"),
                "key_findings": a.get("key_findings"),
                "relevance_score": a.get("relevance_score")
            }
            for a in top5
        ]

        # Build Gemini prompt to summarize key findings
        prompt = (
            f"You are a medical literature analyst. Given these research articles about {molecule_name} for {disease_name}: "
            f"{json.dumps(articles_for_prompt)}\n\n"
            "Summarize the key findings in 3-5 concise bullet points and provide a short overall assessment (one sentence). "
            "Return plain text (no JSON) for the summary."
        )

        raw = ""
        try:
            raw = self._call_gemini(prompt)
        except RuntimeError as e:
            logger.error("Gemini summarization failed: %s", e)
            summary_text = ""
        else:
            clean = self._clean_model_output(raw)
            # keep the summary as-is (text)
            summary_text = clean

        return {"articles": top5, "summary": summary_text}

    # -------------------------
    # Method: get_guidelines
    # -------------------------
    def get_guidelines(self, disease_name: str) -> List[Dict[str, Any]]:
        """
        Return guideline-type 'articles' that match the disease.

        Guidelines are items in pubmed_articles.json with "type": "guideline".
        """
        logger.info("Fetching guidelines for disease=%s", disease_name)
        articles = self._load_articles()
        guidelines = [
            a for a in articles
            if str(a.get("type", "")).strip().lower() == "guideline"
            and str(a.get("disease", "")).strip().lower() == disease_name.strip().lower()
        ]
        return guidelines

    # -------------------------
    # Method: analyze
    # -------------------------
    def analyze(self, molecule_name: str, disease_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Combine literature search and guidelines, ask Gemini to synthesize insights, and return structured result:

        {
          "literature_support": "Strong" | "Moderate" | "Weak",
          "key_findings": list[str],
          "guidelines_alignment": "Aligned" | "Partial" | "Not mentioned",
          "recent_research": list[dict],  # Top 3 articles
          "confidence": float,
          "reasoning": str
        }
        """
        logger.info("Analyzing literature+guidelines for %s in %s", molecule_name, disease_name)

        # 1) Search literature and guidelines
        lit_result = self.search_literature(molecule_name, disease_name)
        top_articles = lit_result.get("articles", [])[:3]  # pick top 3 for synthesis
        literature_summary = lit_result.get("summary", "")

        guidelines = self.get_guidelines(disease_name)

        # Represent these succinctly for the model
        prompt_payload = {
            "articles": [
                {
                    "pmid": a.get("pmid"),
                    "title": a.get("title"),
                    "year": a.get("year"),
                    "journal": a.get("journal"),
                    "key_findings": a.get("key_findings"),
                    "relevance_score": a.get("relevance_score")
                } for a in top_articles
            ],
            "guidelines": [
                {
                    "pmid": g.get("pmid"),
                    "title": g.get("title"),
                    "year": g.get("year"),
                    "key_findings": g.get("key_findings")
                } for g in guidelines
            ]
        }

        # Build main Gemini prompt per user's template
        prompt = (
            f"You are a medical literature analyst. Given these research articles about {molecule_name} for {disease_name}: "
            f"{json.dumps(prompt_payload['articles'])}\n\n"
            f"Assess:\n"
            f"1. Strength of scientific evidence (Strong/Moderate/Weak)\n"
            f"2. Key findings from studies\n"
            f"3. Alignment with FDA guidelines: {json.dumps(prompt_payload['guidelines'])}\n"
            f"4. Overall confidence in biological plausibility\n\n"
            "Return a JSON object with the following structure exactly:\n"
            "{\n"
            "  \"literature_support\": \"Strong|Moderate|Weak\",\n"
            "  \"key_findings\": [\"...\"],\n"
            "  \"guidelines_alignment\": \"Aligned|Partial|Not mentioned\",\n"
            "  \"recent_research\": [ {\"pmid\": \"...\", \"title\": \"...\", \"key_findings\": \"...\"} ],\n"
            "  \"confidence\": 0.0,\n"
            "  \"reasoning\": \"...\"\n"
            "}\n"
            "Make the JSON parsable and do not include any surrounding text or markdown fences."
        )

        # Call Gemini
        try:
            raw = self._call_gemini(prompt)
        except RuntimeError as e:
            logger.error("Gemini synthesis failed: %s", e)
            # fallback: build a conservative local summary
            fallback = {
                "literature_support": "Weak" if not top_articles else "Moderate",
                "key_findings": [a.get("key_findings", "") for a in top_articles],
                "guidelines_alignment": "Aligned" if guidelines else "Not mentioned",
                "recent_research": [
                    {"pmid": a.get("pmid"), "title": a.get("title"), "key_findings": a.get("key_findings")}
                    for a in top_articles
                ],
                "confidence": 0.5,
                "reasoning": "Local fallback: Gemini unavailable or failed; this is a conservative aggregation of results."
            }
            return fallback

        # Clean and parse
        clean = self._clean_model_output(raw)
        try:
            result = json.loads(clean)
        except json.JSONDecodeError:
            logger.error("Failed to parse Gemini output. Raw: %s", raw)
            # Best-effort fallback similar to above
            fallback = {
                "literature_support": "Moderate" if top_articles else "Weak",
                "key_findings": [a.get("key_findings", "") for a in top_articles],
                "guidelines_alignment": "Aligned" if guidelines else "Not mentioned",
                "recent_research": [
                    {"pmid": a.get("pmid"), "title": a.get("title"), "key_findings": a.get("key_findings")}
                    for a in top_articles
                ],
                "confidence": 0.5,
                "reasoning": "Failed to parse Gemini output; returning local aggregated summary."
            }
            return fallback

        # Validate expected keys
        expected_keys = {"literature_support", "key_findings", "guidelines_alignment",
                         "recent_research", "confidence", "reasoning"}
        missing = expected_keys - set(result.keys())
        if missing:
            logger.warning("Gemini synthesis missing expected keys: %s. Returning partial result.", missing)
            # Fill missing pieces from local data
            for k in expected_keys:
                if k not in result:
                    if k == "key_findings":
                        result[k] = [a.get("key_findings", "") for a in top_articles]
                    elif k == "recent_research":
                        result[k] = [
                            {"pmid": a.get("pmid"), "title": a.get("title"), "key_findings": a.get("key_findings")}
                            for a in top_articles
                        ]
                    elif k == "confidence":
                        result[k] = float(result.get("confidence", 0.5))
                    else:
                        result[k] = "N/A"

        # Ensure types
        try:
            result["confidence"] = float(result.get("confidence", 0.0))
        except Exception:
            result["confidence"] = 0.0

        return result


