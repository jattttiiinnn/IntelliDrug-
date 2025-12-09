import asyncio
from typing import Any

class BaseAgent:
    """Base class to provide async support for all agents."""

    def analyze(self, *args, **kwargs) -> Any:
        """
        Synchronous analysis method.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    async def analyze_async(self, *args, **kwargs) -> Any:
        """
        Async wrapper for the synchronous analyze() method.
        Uses asyncio.to_thread() to run blocking code without blocking event loop.
        """
        loop = asyncio.get_running_loop()
        return await asyncio.wait_for(loop.run_in_executor(None, self.analyze, *args, **kwargs), timeout=30)
