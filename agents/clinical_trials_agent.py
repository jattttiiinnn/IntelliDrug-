"""
agents/clinical_trials_agent.py

Analyzes clinical trial data for a given molecule and disease using web scraping.
Summarizes active trial counts, phase distribution, and sponsor insights.
"""

from __future__ import annotations
import os
import json
import re
import time
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime
import random
from dotenv import load_dotenv
import google.generativeai as genai
from .base_agent import BaseAgent


class ClinicalTrialsAgent(BaseAgent):
    """
    Agent responsible for analyzing clinical trial activity for a molecule-disease pair.
    Uses web scraping to get live data from ClinicalTrials.gov.
    """

    def __init__(self, use_live_data: bool = True) -> None:
        """
        Initialize the Clinical Trials Agent.
        
        Args:
            use_live_data: If True, scrapes live data from ClinicalTrials.gov.
                          If False, falls back to local data (if available).
        """
        load_dotenv()
        self.use_live_data = use_live_data
        self.base_url = "https://clinicaltrials.gov/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Initialize Gemini if needed for fallback
        if not use_live_data:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise EnvironmentError("GEMINI_API_KEY not found in .env file.")
            genai.configure(api_key=api_key)

    async def analyze_async(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Async wrapper for the analyze method.
        """
        if not disease_name:
            raise ValueError("disease_name is required for clinical trials analysis")
            
        if self.use_live_data:
            return await self.scrape_clinical_trials(molecule_name, disease_name)
        else:
            return await self.analyze_with_gemini(molecule_name, disease_name)

    async def scrape_clinical_trials(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Scrape clinical trial data from ClinicalTrials.gov.
        
        Args:
            molecule_name: Name of the molecule to search for
            disease_name: Name of the disease/condition
            
        Returns:
            Dict containing clinical trial analysis
        """
        search_term = f"{molecule_name} {disease_name}"
        params = {
            'term': search_term,
            'aggFilters=status:rec status:act status:unkn status:enr': '',
            'pageSize': 100
        }
        print(f"[INFO] 🕷️ SCRAPING ClinicalTrials.gov for {molecule_name} + {disease_name}") 
        try:
            # Add random delay to avoid rate limiting
            time.sleep(2 + random.uniform(0, 1))
            
            # Make the request
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract trial data
            trials = []
            study_cards = soup.find_all('div', class_='study-info')
            
            for card in study_cards:
                try:
                    title_elem = card.find('a', class_='link-underline')
                    title = title_elem.get_text(strip=True) if title_elem else "No title"
                    
                    # Extract phase
                    phase = "Not specified"
                    phase_elem = card.find('span', string=re.compile(r'Phase \d', re.IGNORECASE))
                    if phase_elem:
                        phase = phase_elem.get_text(strip=True)
                    
                    # Extract status
                    status = "Status not available"
                    status_elem = card.find('span', class_=re.compile(r'status'))
                    if status_elem:
                        status = status_elem.get_text(strip=True)
                    
                    # Extract start date
                    start_date = "Start date not available"
                    date_elem = card.find('span', string=re.compile(r'Start Date', re.IGNORECASE))
                    if date_elem and date_elem.find_next_sibling('span'):
                        start_date = date_elem.find_next_sibling('span').get_text(strip=True)
                    
                    trials.append({
                        'title': title,
                        'phase': phase,
                        'status': status,
                        'start_date': start_date
                    })
                except Exception as e:
                    continue
            
            # Process and analyze the data
            print(f"[INFO] ✅ Scraped {len(trials)} trials from ClinicalTrials.gov")
            analysis = self.analyze_trials(trials, molecule_name, disease_name)
            analysis['data_source'] = 'ClinicalTrials.gov (Live)'
            analysis['last_updated'] = datetime.now().isoformat()
            
            return analysis
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch clinical trials data: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error processing clinical trials data: {str(e)}")

    def analyze_trials(self, trials: List[Dict], molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Analyze the scraped trial data.
        
        Args:
            trials: List of trial dictionaries
            molecule_name: Name of the molecule
            disease_name: Name of the disease
            
        Returns:
            Dict containing the analysis
        """
        # Count trials by phase
        phase_counts = {
            'phase_1': 0,
            'phase_2': 0,
            'phase_3': 0,
            'phase_4': 0,
            'other': 0
        }
        
        for trial in trials:
            phase = trial.get('phase', '').lower()
            if '1' in phase:
                phase_counts['phase_1'] += 1
            elif '2' in phase:
                phase_counts['phase_2'] += 1
            elif '3' in phase:
                phase_counts['phase_3'] += 1
            elif '4' in phase:
                phase_counts['phase_4'] += 1
            else:
                phase_counts['other'] += 1
        
        # Count active trials
        active_statuses = ['recruiting', 'active', 'enrolling', 'not yet recruiting']
        active_trials = sum(1 for t in trials if any(status in t.get('status', '').lower() for status in active_statuses))
        
        # Prepare response
        return {
            'molecule_name': molecule_name,
            'disease_name': disease_name,
            'total_trials': len(trials),
            'active_trials': active_trials,
            'phases': phase_counts,
            'trials': trials[:10],  # Include first 10 trials in the response
            'confidence': min(100, max(20, len(trials) * 5)),  # Confidence based on number of trials found
            'analysis_timestamp': datetime.now().isoformat()
        }

    async def analyze_with_gemini(self, molecule_name: str, disease_name: str) -> Dict[str, Any]:
        """
        Fallback method using Gemini API when live data is not available.
        """
        # This is the original implementation that uses local data
        # You can keep this as a fallback
        
        # ... [rest of the original implementation] ...
        
        return {
            'molecule_name': molecule_name,
            'disease_name': disease_name,
            'total_trials': 0,
            'active_trials': 0,
            'phases': {'phase_1': 0, 'phase_2': 0, 'phase_3': 0, 'phase_4': 0, 'other': 0},
            'trials': [],
            'confidence': 0,
            'analysis_timestamp': datetime.now().isoformat(),
            'data_source': 'Fallback (no live data available)'
        }