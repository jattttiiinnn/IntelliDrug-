
import pytest
import os
import sys
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from pathlib import Path

# Add project root to path to allow importing agents
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.clinical_trials_agent import ClinicalTrialsAgent
import requests

@pytest.fixture
def sample_html():
    """Load the sample HTML fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_clinicaltrials_response.html"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")

@pytest.fixture
def agent(mock_env):
    """Create a ClinicalTrialsAgent instance."""
    return ClinicalTrialsAgent(use_live_data=True)

def test_initialization_success(mock_env):
    """Test successful initialization."""
    agent = ClinicalTrialsAgent(use_live_data=True)
    assert agent.use_live_data is True
    assert agent.base_url == "https://clinicaltrials.gov/search"

def test_initialization_fallback_missing_key(monkeypatch):
    """Test initialization fails if Gemini key is missing when use_live_data=False."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # Patch load_dotenv to prevent it from reloading the key from the file
    with patch('agents.clinical_trials_agent.load_dotenv'):
        with pytest.raises(EnvironmentError, match="GEMINI_API_KEY not found"):
            ClinicalTrialsAgent(use_live_data=False)

@pytest.mark.asyncio
async def test_analyze_async_calls_scrape(agent):
    """Test analyze_async calls scrape_clinical_trials when use_live_data is True."""
    with patch.object(agent, 'scrape_clinical_trials', new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = {"full": "report"}
        result = await agent.analyze_async("DrugA", "DiseaseB")
        mock_scrape.assert_awaited_once_with("DrugA", "DiseaseB")
        assert result == {"full": "report"}

@pytest.mark.asyncio
async def test_analyze_async_calls_gemini_fallback(mock_env):
    """Test analyze_async calls analyze_with_gemini when use_live_data is False."""
    agent = ClinicalTrialsAgent(use_live_data=False)
    with patch.object(agent, 'analyze_with_gemini', new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = {"fallback": "report"}
        result = await agent.analyze_async("DrugA", "DiseaseB")
        mock_gemini.assert_awaited_once_with("DrugA", "DiseaseB")
        assert result == {"fallback": "report"}

@pytest.mark.asyncio
async def test_scrape_clinical_trials_success(agent, sample_html):
    """Test successful scraping and parsing of trial data."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        data = await agent.scrape_clinical_trials("DrugX", "DiseaseY")

        assert data['molecule_name'] == "DrugX"
        assert data['disease_name'] == "DiseaseY"
        # We expect 4 valid parsed trials from the fixture (plus 1 ignored malformed one or partial one)
        # Let's check specific counts based on fixture content:
        # 1. Phase 2, Recruiting, Jan 1 2024
        # 2. Not specified (Phase), Active, Feb 15 2023
        # 3. Phase 3, Status not avail, Mar 10 2022
        # 4. Phase 1, Completed, Date not avail
        # 5. Malformed (should be title "No title" or skipped)

        # The code implementation handles exceptions inside the loop with 'continue', so deeply malformed entries might be skipped or have defaults.
        # Trial 5 has no 'a' tag with class 'link-underline', so title="No title". 
        # It's kept but verified fields.
        
        # Check total extracted
        assert len(data['trials']) >= 4 
        
        # Verify first trial details
        t1 = data['trials'][0]
        assert t1['title'] == "Study of Drug X for Disease Y"
        assert t1['phase'] == "Phase 2"
        assert t1['status'] == "Recruiting"
        assert t1['start_date'] == "January 1, 2024"

        # Verify missing phase handling (Trial 2)
        t2 = data['trials'][1]
        assert t2['phase'] == "Not specified"

        # Verify missing status handling (Trial 3)
        t3 = data['trials'][2]
        assert t3['status'] == "Status not available"
        
        # Verify missing date handling (Trial 4)
        t4 = data['trials'][3]
        assert t4['start_date'] == "Start date not available"

        # Verify Analysis stats
        # Phases: Phase 1 (1), Phase 2 (1), Phase 3 (1), Phase 4 (0), Other (1 or 2 depending on malformed)
        assert data['phases']['phase_2'] == 1
        assert data['phases']['phase_3'] == 1

@pytest.mark.asyncio
async def test_scrape_clinical_trials_empty(agent):
    """Test scraping when no trials are found."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = "<html><body><div id='no-results'></div></body></html>"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        data = await agent.scrape_clinical_trials("NonExistentDrug", "RareDisease")
        
        assert data['total_trials'] == 0
        assert data['active_trials'] == 0
        assert data['trials'] == []

@pytest.mark.asyncio
async def test_scrape_clinical_trials_network_timeout(agent):
    """Test handling of network timeout."""
    with patch('requests.get', side_effect=requests.exceptions.Timeout):
        with pytest.raises(RuntimeError, match="Failed to fetch clinical trials data"):
            await agent.scrape_clinical_trials("Drug", "Disease")

@pytest.mark.asyncio
async def test_scrape_clinical_trials_http_429(agent):
    """Test handling of HTTP 429 Too Many Requests."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Client Error")
        mock_get.return_value = mock_response

        with pytest.raises(RuntimeError, match="Failed to fetch clinical trials data"):
            await agent.scrape_clinical_trials("Drug", "Disease")

def test_analyze_trials_logic(agent):
    """Unit test for the analyze_trials helper method logic independently."""
    trials = [
        {'phase': 'Phase 1', 'status': 'Recruiting'},
        {'phase': 'Phase 2', 'status': 'Active, not recruiting'},
        {'phase': 'Early Phase 1', 'status': 'Completed'},  # Counts as phase 1
        {'phase': 'Phase 3', 'status': 'Terminated'},
        {'phase': 'Not Applicable', 'status': 'Enrolling by invitation'},
    ]
    
    analysis = agent.analyze_trials(trials, "TestMol", "TestDis")
    
    assert analysis['molecule_name'] == "TestMol"
    assert analysis['total_trials'] == 5
    
    # Check Phase counts
    # Phase 1: "Phase 1", "Early Phase 1" -> 2
    assert analysis['phases']['phase_1'] == 2
    # Phase 2: 1
    assert analysis['phases']['phase_2'] == 1
    # Phase 3: 1
    assert analysis['phases']['phase_3'] == 1
    # Other: 1
    assert analysis['phases']['other'] == 1
    
    # Check Active trials
    # Active statuses checked: 'recruiting', 'active', 'enrolling', 'not yet recruiting'
    # 1. Recruiting -> Active
    # 2. Active, not recruiting -> Active
    # 3. Completed -> Inactive
    # 4. Terminated -> Inactive
    # 5. Enrolling... -> Active
    assert analysis['active_trials'] == 3
