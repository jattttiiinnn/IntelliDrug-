"""
conversation_manager.py

Manages conversation history and handles agent-specific queries.
"""
from typing import Dict, List, Optional, TypedDict
import google.generativeai as genai

class Message(TypedDict):
    role: str  # 'user' or 'assistant'
    content: str
    agent: Optional[str]  # Which agent is responding

class ConversationManager:
    def __init__(self):
        self.conversations: Dict[str, List[Message]] = {}
        self.agent_contexts: Dict[str, Dict] = {}
    
    def _get_conversation_key(self, molecule: str, disease: str) -> str:
        """Generate a unique key for a conversation."""
        return f"{molecule.lower()}_{disease.lower()}"
    
    def get_conversation(self, molecule: str, disease: str) -> List[Message]:
        """Get conversation history for a specific molecule and disease."""
        key = self._get_conversation_key(molecule, disease)
        return self.conversations.get(key, [])
    
    def add_message(self, molecule: str, disease: str, role: str, content: str, agent: str = None) -> None:
        """Add a message to the conversation history."""
        key = self._get_conversation_key(molecule, disease)
        if key not in self.conversations:
            self.conversations[key] = []
        
        self.conversations[key].append({
            'role': role,
            'content': content,
            'agent': agent
        })
    
    async def get_agent_response(
        self,
        molecule: str,
        disease: str,
        agent_name: str,
        user_question: str,
        context: Dict
    ) -> str:
        """
        Get a response from the specified agent using the Gemini model.
        
        Args:
            molecule: Name of the molecule being analyzed
            disease: Name of the target disease
            agent_name: Name of the agent (e.g., 'patent', 'clinical')
            user_question: The user's question
            context: Agent-specific context data
            
        Returns:
            The agent's response as a string
        """
        # Add user's question to conversation history
        self.add_message(molecule, disease, 'user', user_question)
        
        # Prepare the prompt for the agent
        prompt = self._prepare_agent_prompt(agent_name, user_question, context)
        
        try:
            # Call Gemini API
            model = genai.GenerativeModel('gemini-pro')
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            # Get the response text
            response_text = response.text.strip()
            
            # Add agent's response to conversation history
            self.add_message(molecule, disease, 'assistant', response_text, agent_name)
            
            return response_text
            
        except Exception as e:
            error_msg = f"Error getting response from {agent_name} agent: {str(e)}"
            self.add_message(molecule, disease, 'assistant', error_msg, agent_name)
            return error_msg
    
    def _prepare_agent_prompt(self, agent_name: str, question: str, context: Dict) -> str:
        """Prepare the prompt for the agent based on its type."""
        base_prompt = f"""You are an expert {agent_name.replace('_', ' ').title()} analyst. 
        Answer the following question based on your expertise and the provided context.
        Be concise but thorough in your response.
        
        Question: {question}
        
        Context:
        {context}
        
        Your response:"""
        
        return base_prompt.format(question=question, context=str(context))
