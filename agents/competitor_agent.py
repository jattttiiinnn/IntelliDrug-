"""
agents/competitor_agent.py

Agent responsible for tracking competitor activities and clinical trials.
Uses ClinicalTrials.gov API v2.
"""

import os
import json
import time
import logging
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Check if BaseAgent exists, otherwise use a simple base
try:
    from .base_agent import BaseAgent
except ImportError:
    class BaseAgent:
        def analyze_async(self, *args, **kwargs):
            raise NotImplementedError

# ======================================================================================
# DATA MODELS
# ======================================================================================

@dataclass
class CompetitorTrial:
    drug_name: str
    indication: str
    phase: str
    status: str
    start_date: str
    sponsor: str
    title: str = ""
    nct_id: str = ""

@dataclass
class CompetitorAlert:
    competitor_name: str
    action_type: str  # e.g., "New Trial", "Status Change", "Phase Advancements"
    drug_name: str
    date: str
    severity: str # "High", "Medium", "Low"
    details: str = ""

# ======================================================================================
# COMPETITOR AGENT
# ======================================================================================

class CompetitorAgent(BaseAgent):
    """
    Agent for analyzing competitor clinical trials and activities.
    """

    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize the Competitor Agent.
        
        Args:
            cache_dir: Directory to store cache files.
        """
        load_dotenv()
        
        # Initialize Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            logger.warning("GEMINI_API_KEY not found. Gemini features will be disabled.")

        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) InteliDrugBot/1.0'
        }
        
        # Setup caching
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, "competitor_cache.json")
        self._load_cache()

    def _load_cache(self):
        """Load cache from JSON file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except json.JSONDecodeError:
                self.cache = {}
        else:
            self.cache = {}

    def _save_cache(self):
        """Save cache to JSON file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _get_cached_response(self, key: str) -> Optional[Any]:
        """Get data from cache if valid (less than 24 hours old)."""
        if key in self.cache:
            entry = self.cache[key]
            timestamp = datetime.fromisoformat(entry['timestamp'])
            if datetime.now() - timestamp < timedelta(hours=24):
                return entry['data']
        return None

    def _set_cached_response(self, key: str, data: Any):
        """Save data to cache."""
        self.cache[key] = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self._save_cache()

    def _parse_api_study(self, study: Dict[str, Any], search_term: str, category: str) -> Optional[CompetitorTrial]:
        """Parse a single study from API response."""
        try:
            protocol = study.get('protocolSection', {})
            
            # Identification
            ident = protocol.get('identificationModule', {})
            nct_id = ident.get('nctId', '')
            title = ident.get('officialTitle') or ident.get('briefTitle', 'No Title')
            
            # Status
            status_mod = protocol.get('statusModule', {})
            status = status_mod.get('overallStatus', 'Unknown')
            start_date_struct = status_mod.get('startDateStruct', {})
            start_date = start_date_struct.get('date', 'Unknown')
            
            # Sponsor
            sponsor_mod = protocol.get('sponsorCollaboratorsModule', {})
            sponsor = sponsor_mod.get('leadSponsor', {}).get('name', 'Unknown')
            
            # Design (Phase)
            design_mod = protocol.get('designModule', {})
            phases_list = design_mod.get('phases', [])
            phase = ", ".join(phases_list) if phases_list else "Not Specified"
            
            # Interventions (for Drug Name if searching by Indication)
            interventions = protocol.get('armsInterventionsModule', {}).get('interventions', [])
            drug_names = [i.get('name') for i in interventions if i.get('type') == 'DRUG']
            
            # Determining fields based on search category
            if category == 'drug':
                drug_name_val = search_term
                indication_val = "Target Condition"
                # Ideally extract conditions
                conditions = protocol.get('conditionsModule', {}).get('conditions', [])
                if conditions:
                     indication_val = ", ".join(conditions[:2])
            else:
                drug_name_val = ", ".join(drug_names) if drug_names else "Experimental"
                indication_val = search_term

            return CompetitorTrial(
                drug_name=drug_name_val,
                indication=indication_val,
                phase=phase,
                status=status,
                start_date=start_date,
                sponsor=sponsor,
                title=title,
                nct_id=nct_id
            )
        except Exception as e:
            logger.debug(f"Error parsing study {study.get('protocolSection', {}).get('identificationModule', {}).get('nctId')}: {e}")
            return None

    def _fetch_api(self, params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Internal method to call API."""
        try:
            logger.info(f"Calling API with params: {params}")
            resp = requests.get(self.base_url, params=params, headers=self.headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data.get('studies', [])
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return []

    def search_trials_by_drug(self, drug_name: str) -> List[CompetitorTrial]:
        """Search for trials involving a specific drug."""
        cache_key = f"api_drug_{drug_name}"
        cached = self._get_cached_response(cache_key)
        if cached:
            return [CompetitorTrial(**item) for item in cached]

        # API query for intervention/treatment
        params = {
            'query.intr': drug_name,
            'pageSize': 50
        }
        
        studies = self._fetch_api(params)
        results = []
        for s in studies:
            trial = self._parse_api_study(s, drug_name, category='drug')
            if trial:
                results.append(trial)
        
        self._set_cached_response(cache_key, [asdict(r) for r in results])
        return results

    def search_trials_by_indication(self, indication: str) -> List[CompetitorTrial]:
        """Search for trials related to a specific indication/disease."""
        cache_key = f"api_cond_{indication}"
        cached = self._get_cached_response(cache_key)
        if cached:
            return [CompetitorTrial(**item) for item in cached]

        # API query for condition
        params = {
            'query.cond': indication,
            'filter.overallStatus': ",".join(['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION']), # Active
            'pageSize': 50
        }
        
        studies = self._fetch_api(params)
        results = []
        for s in studies:
            trial = self._parse_api_study(s, indication, category='indication')
            if trial:
                results.append(trial)
        
        self._set_cached_response(cache_key, [asdict(r) for r in results])
        return results

    # ==================================================================================
    # COMPETITIVE INTELLIGENCE EXTENSIONS
    # ==================================================================================

    def track_competitor_molecule(self, drug_name: str) -> Dict[str, Any]:
        """
        Monitor specific drug - returns aggregated status.
        """
        trials = self.search_trials_by_drug(drug_name)
        
        # Find highest phase
        max_phase = "Unknown"
        phase_map = {"PHASE1": 1, "PHASE2": 2, "PHASE3": 3, "PHASE4": 4}
        highest_val = 0
        
        active_count = 0
        latest_start = "1900-01-01"
        sponsors = set()

        for t in trials:
            # Check Phase
            p_clean = t.phase.replace(" ", "").upper()
            for key, val in phase_map.items():
                if key in p_clean:
                    if val > highest_val:
                        highest_val = val
                        max_phase = f"Phase {val}"
            
            # Active Count (heuristic from scraped status)
            if "RECRUITING" in t.status.upper() or "ACTIVE" in t.status.upper():
                active_count += 1
                
            # Latest Start
            if t.start_date and t.start_date != "Unknown":
                # Only compare if format allows, keeping distinct logic simple
                # CT.gov often returns YYYY-MM or YYYY-MM-DD
                if t.start_date > latest_start:
                    latest_start = t.start_date
            
            sponsors.add(t.sponsor)

        return {
            "drug_name": drug_name,
            "highest_phase": max_phase,
            "active_trials_count": active_count,
            "latest_trial_date": latest_start if latest_start != "1900-01-01" else "N/A",
            "sponsors": list(sponsors)
        }

    def find_competing_indications(self, indication: str) -> List[Dict[str, Any]]:
        """
        Find all drugs targeting the same disease.
        Returns list of competitors with basic stats.
        """
        trials = self.search_trials_by_indication(indication)
        competitors = {} # name -> count

        for t in trials:
            # Split comma separated drugs
            for d in t.drug_name.split(','):
                d = d.strip()
                if len(d) > 3 and "Placebo" not in d and "Standard of Care" not in d:
                    competitors[d] = competitors.get(d, 0) + 1
        
        # Sort by frequency
        sorted_comps = sorted(competitors.items(), key=lambda x: x[1], reverse=True)
        return [{"drug": k, "trial_count": v} for k,v in sorted_comps]

    def detect_new_trials(self, trials: List[CompetitorTrial], days: int = 90) -> List[CompetitorTrial]:
        """Identify trials started in the last X days."""
        new_trials = []
        cutoff = datetime.now() - timedelta(days=days)
        
        for t in trials:
            # Parse start date (formats vary: YYYY-MM-DD, YYYY-MM, YYYY)
            try:
                date_str = t.start_date
                if not date_str or date_str == "Unknown":
                    continue
                
                parts = date_str.split('-')
                if len(parts) == 3:
                   d = datetime.strptime(date_str, "%Y-%m-%d")
                elif len(parts) == 2:
                   d = datetime.strptime(date_str, "%Y-%m")
                else:
                   continue # Skip year-only for "new" detection to be safe
                
                if d >= cutoff:
                    new_trials.append(t)
            except ValueError:
                continue
                
        return new_trials

    def calculate_threat_score(self, competitor_drug: str, target_indication: str) -> int:
        """
        Calculate competitive threat score (0-100).
        Based on: Max Phase, Number of Trials, Recency.
        """
        # Fetch agg data
        # Note: This calls search internally, might hit cache
        info = self.track_competitor_molecule(competitor_drug)
        
        score = 0
        
        # 1. Phase Score (Max 50)
        p = info['highest_phase']
        if "Phase 3" in p: score += 50
        elif "Phase 2" in p: score += 30
        elif "Phase 1" in p: score += 10
        
        # 2. Activity Score (Max 30)
        # Cap at 10 active trials
        score += min(30, info['active_trials_count'] * 3)
        
        # 3. Recency Score (Max 20)
        # If latest trial is within last year
        if info['latest_trial_date'] != "N/A":
             try:
                 # rough check
                 year = int(info['latest_trial_date'].split('-')[0])
                 if year >= datetime.now().year - 1:
                     score += 20
             except:
                 pass
                 
        return min(100, score)

    def generate_alerts(self, trials: List[CompetitorTrial]) -> List[CompetitorAlert]:
        """
        Generate alerts based on trial data (New Phase 3, etc).
        """
        alerts = []
        new_trials = self.detect_new_trials(trials, days=60) # Last 60 days
        
        for t in new_trials:
            severity = "Low"
            action = "New Trial Detected"
            
            if "PHASE3" in t.phase.replace(" ","").upper():
                severity = "High"
                action = "New Phase 3 Trial"
            elif "PHASE2" in t.phase.replace(" ","").upper():
                severity = "Medium"
                action = "New Phase 2 Trial"
            
            alerts.append(CompetitorAlert(
                competitor_name=t.sponsor,
                action_type=action,
                drug_name=t.drug_name,
                date=t.start_date,
                severity=severity,
                details=f"Title: {t.title} ({t.nct_id})"
            ))
            
        return alerts

    def generate_summary_report(self, molecule: str, indication: str, competitors: List[Dict], alerts: List[CompetitorAlert]) -> str:
        """
        Generate a natural language summary string.
        """
        lines = []
        lines.append(f"### Competitive Landscape: {molecule} in {indication}")
        
        # Competitor count
        lines.append(f"**Competitors Identified**: {len(competitors)} drugs actively targeting {indication}.")
        
        # Top 3
        if competitors:
            top_3 = competitors[:3]
            names = [c['drug'] for c in top_3]
            lines.append(f"**Top Competitors**: {', '.join(names)}")
        
        # Alerts
        high_alerts = [a for a in alerts if a.severity == "High"]
        if high_alerts:
             lines.append(f"**⚠️ CRITICAL UPDATES**: {len(high_alerts)} new key developments.")
             for a in high_alerts[:2]:
                 lines.append(f"- {a.action_type}: {a.drug_name} by {a.competitor_name}")
        
        # Threat assessment
        # Find highest threat
        max_threat = 0
        threat_drug = "None"
        for c in competitors[:5]:
             s = self.calculate_threat_score(c['drug'], indication)
             if s > max_threat:
                 max_threat = s
                 threat_drug = c['drug']
        
        if max_threat > 0:
            lines.append(f"**Highest Threat**: {threat_drug} (Score: {max_threat}/100)")
            
        return "\n\n".join(lines)

    def analyze_async(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Main entry point for agent execution.
        """
        logger.info(f"Analyzing competitors for {molecule_name} in {disease_name}")
        
        # 1. Broad Search
        trials = self.search_trials_by_indication(disease_name)
        
        # 2. Identify Competitors
        competitors_list = self.find_competing_indications(disease_name)
        
        # 3. Filter out self (the molecule we are analyzing)
        competitors_list = [c for c in competitors_list if molecule_name.lower() not in c['drug'].lower()]
        
        # 4. Generate Alerts
        alerts = self.generate_alerts(trials)
        
        # 5. Calculate Activity Stats
        phases = {}
        for t in trials:
            p = t.phase
            phases[p] = phases.get(p, 0) + 1
            
        # 6. Generate Report
        summary = self.generate_summary_report(molecule_name, disease_name, competitors_list, alerts)
        
        return {
            "competitor_analysis": {
                "total_active_trials": len(trials),
                "phase_breakdown": phases,
                "top_competitors": competitors_list[:5],
                "alerts": [asdict(a) for a in alerts],
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }
        }

if __name__ == "__main__":
    # Test script usage
    agent = CompetitorAgent()
    
    print("\n--- TEST SCENARIO: Track all competitors for Metformin in NASH ---")
    
    # 1. Run main analysis (simulates agent call)
    result = agent.analyze_async("Metformin", "NASH") # Non-alcoholic Steatohepatitis
    
    analysis = result['competitor_analysis']
    print("\n[Summary Report]")
    print(analysis['summary'])
    
    print("\n[Top Competitors]")
    for c in analysis['top_competitors']:
        score = agent.calculate_threat_score(c['drug'], "NASH")
        print(f"- {c['drug']}: {c['trial_count']} trials (Threat: {score}/100)")
    
    print("\n[Alerts]")
    for a in analysis['alerts']:
        print(f"[{a['severity']}] {a['action_type']} - {a['drug_name']}")

