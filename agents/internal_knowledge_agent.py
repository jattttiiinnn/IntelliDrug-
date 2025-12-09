import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class InternalKnowledgeAgent(BaseAgent):
    """
    Agent for searching and summarizing internal company knowledge.
    Operates on markdown documents stored in data/internal_docs/.
    """

    def __init__(self, docs_dir: str = "data/internal_docs"):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not found in .env file.")
        genai.configure(api_key=api_key)
        
        self.docs_dir = docs_dir
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def analyze_async(self, molecule_name: str, disease_name: str = None) -> Dict[str, any]:
        """
        Async wrapper for the analyze method.
        
        Args:
            molecule_name: Name of the molecule to analyze
            disease_name: Optional disease name
            
        Returns:
            Dict containing internal knowledge analysis
        """
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.analyze, molecule_name, disease_name)

    # ------------------------------
    # Utility: Search all markdown files
    # ------------------------------
    def search_documents(self, query_text: str, molecule_name: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Search all .md files for relevant excerpts.
        Returns a list of dicts with filename and text excerpts.
        """
        results = []
        query_text = query_text.lower()
        if molecule_name:
            molecule_name = molecule_name.lower()

        try:
            for filename in os.listdir(self.docs_dir):
                if not filename.endswith(".md"):
                    continue
                filepath = os.path.join(self.docs_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    if query_text in line_lower or (molecule_name and molecule_name in line_lower):
                        # Get 2 lines before and after match for context
                        start = max(i - 2, 0)
                        end = min(i + 3, len(lines))
                        excerpt = "".join(lines[start:end]).strip()
                        results.append({
                            "file": filename,
                            "excerpt": excerpt
                        })
                        break  # one hit per file is enough
        except Exception as e:
            logger.error(f"Error searching documents: {e}")

        return results

    # ------------------------------
    # Utility: Find past analyses for molecule
    # ------------------------------
    def get_past_analyses(self, molecule_name: str) -> List[str]:
        """
        Searches internal docs for past analyses related to the given molecule.
        Returns list of past outcomes or key learnings.
        """
        analyses = []
        try:
            for filename in os.listdir(self.docs_dir):
                if not filename.endswith(".md"):
                    continue
                if molecule_name.lower() in filename.lower():
                    filepath = os.path.join(self.docs_dir, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Extract sections if keywords appear
                        if "outcome" in content.lower():
                            start = content.lower().find("outcome")
                            snippet = content[start:start + 300]
                            analyses.append(snippet.strip())
                        if "key learning" in content.lower():
                            start = content.lower().find("key learning")
                            snippet = content[start:start + 300]
                            analyses.append(snippet.strip())
        except Exception as e:
            logger.error(f"Error retrieving past analyses: {e}")
        return analyses

    # ------------------------------
    # Main: Analyze internal knowledge
    # ------------------------------
    def analyze(self, molecule_name: str, disease_name: Optional[str] = None) -> Dict:
        """
        Combines document search and past analyses.
        Sends context to Gemini for summarization.
        Returns structured internal knowledge analysis.
        """
        logger.info(f"Running InternalKnowledgeAgent for {molecule_name} - {disease_name}")

        # Step 1: Collect internal docs
        docs = self.search_documents(disease_name, molecule_name)
        past_data = self.get_past_analyses(molecule_name)

        if not docs and not past_data:
            logger.warning("No internal knowledge found.")
            return {
                "past_experience": "None",
                "past_outcomes": [],
                "manufacturing_capability": "Requires assessment",
                "strategic_alignment": "Low",
                "internal_insights": [],
                "confidence": 0.4
            }

        # Step 2: Prepare text context for Gemini
        combined_text = "\n\n".join([f"{d['file']}:\n{d['excerpt']}" for d in docs])
        if past_data:
            combined_text += "\n\nPast Analyses:\n" + "\n".join(past_data)

        prompt = f"""
You are a medical literature analyst. Given these internal company documents about {molecule_name} for {disease_name}:
{combined_text}

Summarize:
1. Past company experience with this molecule
2. Manufacturing capability status
3. Strategic fit with portfolio
4. Key internal insights

Return JSON with structure:
{{
  "past_experience": "Available" | "None",
  "past_outcomes": list[str],
  "manufacturing_capability": "Confirmed" | "Requires assessment",
  "strategic_alignment": "High" | "Medium" | "Low",
  "internal_insights": list[str],
  "confidence": float
}}
"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Try parsing JSON safely
            result = None
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                # fallback: regex cleaning or default
                logger.warning("Gemini output not valid JSON; returning fallback structure.")
                result = {
                    "past_experience": "Available" if past_data else "None",
                    "past_outcomes": past_data,
                    "manufacturing_capability": "Confirmed" if any("manufacturing" in d["excerpt"].lower() for d in docs) else "Requires assessment",
                    "strategic_alignment": "High" if "strategy" in combined_text.lower() else "Medium",
                    "internal_insights": [d["excerpt"][:150] for d in docs[:3]],
                    "confidence": 0.75
                }

            result["timestamp"] = datetime.utcnow().isoformat() + "Z"
            return result

        except Exception as e:
            logger.error(f"InternalKnowledgeAgent failed: {e}")
            return {
                "past_experience": "None",
                "past_outcomes": [],
                "manufacturing_capability": "Requires assessment",
                "strategic_alignment": "Low",
                "internal_insights": [],
                "confidence": 0.0,
                "error": str(e)
            }
