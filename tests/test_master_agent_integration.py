
import pytest
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from master_agent import MasterAgent, AnalysisStrategy

@pytest.fixture
def mock_agent_result():
    return {
        "confidence": 0.8,
        "findings": [
            {"finding": "Strong positive signal", "evidence_strength": 85, "is_positive": True},
            {"finding": "Minor risk factor", "evidence_strength": 30, "is_positive": False}
        ],
        "active_trials": 5, # for clinical
        "patent_status": "Active", # for patent
        "opportunity_score": 75 # for market
    }

@pytest.fixture
def master_agent(mock_agent_result):
    """Create master agent with mocked workers."""
    agent = MasterAgent()
    
    # Mock all sub-agents
    mock_agents = {}
    for name in agent.agents:
        mock_sub = AsyncMock()
        mock_sub.analyze_async.return_value = mock_agent_result.copy()
        mock_agents[name] = mock_sub
        
    agent.agents = mock_agents
    
    # Mock report generator (sync method running in thread)
    agent.report_generator = MagicMock()
    agent.report_generator.generate_report.return_value = "/path/to/report.pdf"
    
    return agent

@pytest.mark.asyncio
async def test_analyze_repurposing_async_success(master_agent):
    """Scenario 1: All 6 agents complete successfully."""
    # Run analysis
    result = await master_agent.analyze_repurposing_async("DrugA", "DiseaseB")
    
    # Verify basics
    assert result["molecule"] == "DrugA"
    assert result["disease"] == "DiseaseB"
    assert result["pdf_report"] == "/path/to/report.pdf"
    
    # Verify synthesis
    synthesis = result["synthesis"]
    assert synthesis["recommendation"] == "PROCEED"
    assert synthesis["score"] > 0
    assert "Active in 5 clinical trials" in synthesis["strengths"]
    
    # Verify all agents were called
    for name, mock in master_agent.agents.items():
        mock.analyze_async.assert_awaited_once_with("DrugA", "DiseaseB")

@pytest.mark.asyncio
async def test_analyze_repurposing_async_partial_failure(master_agent):
    """Scenario 2: One agent fails, others continue (graceful degradation)."""
    # Make patent agent fail
    master_agent.agents["patent_analysis"].analyze_async.side_effect = Exception("Database Connection Error")
    
    result = await master_agent.analyze_repurposing_async("DrugA", "DiseaseB")
    
    # Patent should have error
    assert result["patent_analysis"]["confidence"] == 0.0
    assert "Database Connection Error" in result["patent_analysis"]["error"]
    
    # Others should succeed
    assert result["clinical_analysis"]["confidence"] == 0.8
    
    # Synthesis should still work (might have lower confidence/score)
    assert "synthesis" in result

@pytest.mark.asyncio
async def test_analyze_repurposing_async_timeout(master_agent):
    """Scenario 4: Timeout handling for slow agents."""
    # Simulate timeout by raising asyncio.TimeoutError
    master_agent.agents["market_analysis"].analyze_async.side_effect = asyncio.TimeoutError()
    
    result = await master_agent.analyze_repurposing_async("DrugA", "DiseaseB")
    
    assert result["market_analysis"]["error"] == "Timeout"
    assert result["market_analysis"]["confidence"] == 0.0
    
    # Verify progress tracking set to failed
    assert master_agent.progress["market_analysis"] == "Failed"
    assert master_agent.progress["clinical_analysis"] == "Complete"

@pytest.mark.asyncio
async def test_compare_molecules_async(master_agent):
    """Scenario 7: Compare mode with 2 molecules."""
    molecules = ["DrugA", "DrugB"]
    
    result = await master_agent.compare_molecules_async(molecules, "DiseaseC")
    
    assert "comparison_metadata" in result
    assert result["comparison_metadata"]["molecules"] == molecules
    
    # Check individual results are present
    assert "DrugA" in result
    assert "DrugB" in result
    
    # Check comparison synthesis
    comp_synth = result["comparison_synthesis"]
    assert "best_candidates" in comp_synth
    assert len(comp_synth["comparison"]) == 2

@pytest.mark.asyncio
async def test_progress_tracking(master_agent):
    """Scenario 5: Progress tracking updates correctly."""
    # Check initial state
    assert all(status == "Pending" for status in master_agent.progress.values())
    
    # Run analysis
    await master_agent.analyze_repurposing_async("DrugA", "DiseaseB")
    
    # Check final state (all Complete)
    assert all(status == "Complete" for status in master_agent.progress.values())

@pytest.mark.asyncio
async def test_rate_limit_fallback_logic(master_agent):
    """Scenario 3: Rate limit fallback (simulated logic check)."""
    # NOTE: The MasterAgent itself doesn't have explicit logic to retry with fallback 
    # if one agent fails with 429, unless _run_agent_async implements it or the agent does.
    # Looking at master_agent.py, _run_agent_async just catches exceptions.
    # However, we can verify that the error propagates correctly as a 'Failed' state.
    
    master_agent.agents["web_analysis"].analyze_async.side_effect = Exception("429 Too Many Requests")
    
    result = await master_agent.analyze_repurposing_async("DrugA", "DiseaseB")
    
    assert "429 Too Many Requests" in result["web_analysis"]["error"]
    assert master_agent.progress["web_analysis"] == "Failed"

def test_synthesis_logic(master_agent):
    """Scenario 6: Result synthesis with mock data."""
    # Manually construct a results dict
    results = {
        "patent_analysis": {"confidence": 0.9, "patent_status": "Active"},
        "clinical_analysis": {"confidence": 0.2, "findings": [{"finding": "Toxic", "evidence_strength": 90, "is_positive": False}]},
        "market_analysis": {"confidence": 0.8},
        "web_analysis": {"confidence": 0.5},
        "exim_analysis": {"confidence": 0.5},
        "internal_analysis": {"confidence": 0.5},
        "molecule": "Test",
        "disease": "Test"
    }
    
    synth = master_agent.synthesize_results(results, AnalysisStrategy.STANDARD)
    
    # Confidence should be pulled down by clinical
    assert synth["confidence"] < 0.9
    
    # Should detect weakness
    assert "Toxic" in synth["weaknesses"]
    
    # Should detect patent strength
    assert "Active patent protection" in synth["strengths"]
