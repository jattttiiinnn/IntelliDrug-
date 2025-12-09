"""
test_all_agents.py

Comprehensive test script to verify all agents are working correctly.
Tests both synchronous and asynchronous methods for each agent.
"""

import asyncio
import sys
from typing import Dict, Any
from datetime import datetime

# Import all agents
from agents.patent_agent import PatentAgent
from agents.clinical_trials_agent import ClinicalTrialsAgent
from agents.market_agent import MarketAgent
from agents.exim_agent import EXIMAgent
from agents.web_intelligence_agent import WebIntelligenceAgent
from agents.internal_knowledge_agent import InternalKnowledgeAgent
from master_agent import MasterAgent

# Test configuration
TEST_MOLECULE = "Metformin"
TEST_DISEASE = "NASH"

class TestRunner:
    """Helper class to run agent tests with consistent formatting."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.start_time = datetime.now()
        self.terminal_width = 80
        self.setup_printing()
        
    def setup_printing(self):
        """Set up pretty printing with a divider."""
        try:
            import shutil
            self.terminal_width = min(100, shutil.get_terminal_size().columns)
        except:
            self.terminal_width = 80
            
    def print_header(self, text: str):
        """Print a section header."""
        print("\n" + "=" * self.terminal_width)
        print(f" {text} ".center(self.terminal_width, "="))
        print("=" * self.terminal_width)
        
    def print_test_result(self, test_name: str, success: bool, error: str = None):
        """Print the result of a single test."""
        status = "PASSED" if success else "FAILED"
        color_code = "\033[92m" if success else "\033[91m"
        reset_code = "\033[0m"
        
        print(f"{test_name}: {color_code}{status}{reset_code}")
        if error and not success:
            print(f"  Error: {error}")
            
        if success:
            self.passed += 1
        else:
            self.failed += 1
    
    async def test_agent_sync(self, agent, agent_name: str, molecule: str, disease: str) -> bool:
        """Test the synchronous analyze method of an agent."""
        try:
            result = agent.analyze(molecule, disease)
            assert isinstance(result, dict), "Result should be a dictionary"
            return True, None
        except Exception as e:
            return False, str(e)
            
    async def test_agent_async(self, agent, agent_name: str, molecule: str, disease: str) -> bool:
        """Test the asynchronous analyze_async method of an agent."""
        try:
            result = await agent.analyze_async(molecule, disease)
            assert isinstance(result, dict), "Result should be a dictionary"
            return True, None
        except Exception as e:
            return False, str(e)
    
    def print_summary(self):
        """Print a summary of test results."""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        duration = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "=" * self.terminal_width)
        print(" TEST SUMMARY ".center(self.terminal_width, "="))
        print("=" * self.terminal_width)
        print(f"Total tests: {total}")
        print(f"Passed: \033[92m{self.passed}\033[0m")
        print(f"Failed: \033[91m{self.failed}\033[0m")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        print("=" * self.terminal_width + "\n")
        
        return self.failed == 0

async def test_all_agents():
    """Run tests for all individual agents."""
    runner = TestRunner()
    agents = {
        "PatentAgent": PatentAgent(),
        "ClinicalTrialsAgent": ClinicalTrialsAgent(),
        "MarketAgent": MarketAgent(),
        "EXIMAgent": EXIMAgent(),
        "WebIntelligenceAgent": WebIntelligenceAgent(),
        "InternalKnowledgeAgent": InternalKnowledgeAgent()
    }
    
    # Test each agent's sync and async methods
    for agent_name, agent in agents.items():
        runner.print_header(f"Testing {agent_name}")
        
        # Test sync analyze
        success, error = await runner.test_agent_sync(
            agent, agent_name, TEST_MOLECULE, TEST_DISEASE
        )
        runner.print_test_result(
            f"{agent_name}.analyze()", 
            success, 
            error
        )
        
        # Test async analyze_async
        success, error = await runner.test_agent_async(
            agent, agent_name, TEST_MOLECULE, TEST_DISEASE
        )
        runner.print_test_result(
            f"{agent_name}.analyze_async()", 
            success, 
            error
        )
    
    return runner

async def test_master_agent():
    """Test MasterAgent coordination"""
    master = MasterAgent()
    
    # Test sync version
    print("Testing MasterAgent.analyze_repurposing() (sync)...")
    try:
        result = master.analyze_repurposing(TEST_MOLECULE, TEST_DISEASE)
        if isinstance(result, dict) and "master_synthesis" in result:
            print(" MasterAgent.analyze_repurposing(): PASSED")
            return True, None
        else:
            error = "Invalid result structure"
            print(f" MasterAgent.analyze_repurposing(): FAILED - {error}")
            return False, error
    except Exception as e:
        print(f" MasterAgent.analyze_repurposing(): FAILED - {str(e)}")
        return False, str(e)
    
    # Rest of your test...
    
    # Test async version
    print("Testing MasterAgent.analyze_repurposing_async() (async)...")
    try:
        result = await master.analyze_repurposing_async(TEST_MOLECULE, TEST_DISEASE)
        if isinstance(result, dict) and "master_synthesis" in result:
            print(" MasterAgent.analyze_repurposing_async(): PASSED")
            return True, None
        else:
            error = "Invalid result structure"
            print(f" MasterAgent.analyze_repurposing_async(): FAILED - {error}")
            return False, error
    except Exception as e:
        print(f" MasterAgent.analyze_repurposing_async(): FAILED - {str(e)}")
        return False, str(e)

async def main():
    """Main test function."""
    print(f"\n{' STARTING AGENT TESTS ':=^{80}}")
    print(f"Testing with molecule: {TEST_MOLECULE}")
    print(f"Testing with disease: {TEST_DISEASE}\n")
    
    # Run individual agent tests
    agent_runner = await test_all_agents()
    
    # Run MasterAgent tests
    print("\n" + "=" * 80)
    print(" TESTING MASTER AGENT ".center(80, "="))
    print("=" * 80)
    
    master_success = True
    master_errors = []
    
    # Test MasterAgent
    try:
        success, error = await test_master_agent()
        if not success:
            master_success = False
            if error:
                master_errors.append(error)
    except Exception as e:
        master_success = False
        master_errors.append(str(e))
    
    # Print summaries
    agent_runner.print_summary()
    
    # Print MasterAgent test results
    print("\n" + "=" * 80)
    print(" MASTER AGENT TEST RESULTS ".center(80, "="))
    print("=" * 80)
    
    if master_success:
        print("\n\033[92mAll MasterAgent tests passed successfully!\033[0m")
    else:
        print("\n\033[91mSome MasterAgent tests failed:\033[0m")
        for error in master_errors:
            print(f"  - {error}")
    
    # Exit with appropriate status code
    if agent_runner.failed > 0 or not master_success:
        print("\n\033[91mSome tests failed. Please check the output above.\033[0m")
        sys.exit(1)
    else:
        print("\n\033[92mAll tests passed successfully!\033[0m")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())