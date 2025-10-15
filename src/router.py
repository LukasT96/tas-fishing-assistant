"""
Router - LLM-based routing logic

Determines which resources to use for answering user queries:
    - RAG only: Answer from documents
    - Tool only: Use external tool/API
    - RAG + Tool: Combine both approaches

Uses prompt-driven routing (no hard-coded rules) via LLM decision-making.
"""

import json
import os
from typing import Dict, Optional
from groq import Groq
from google import genai
from dotenv import load_dotenv
import yaml

from src.prompts import ROUTING_PROMPT

load_dotenv()


class Router:
    """
    LLM-based router that decides which resources to use for answering queries.
    
    The router analyzes user questions and determines:
    - Whether to retrieve from documents (RAG)
    - Whether to call a tool
    - Which tool to call and with what parameters
    """
    
    def __init__(self, config_path: str = "config.yml"):
        """Initialize the router with LLM clients"""
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get API keys
        groq_api_key = os.getenv("GROQ_API_KEY")
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not groq_api_key or not gemini_api_key:
            raise ValueError("API keys not found in .env file")
        
        # Initialize LLM clients
        self.groq_client = Groq(api_key=groq_api_key)
        self.gemini_client = genai.Client(api_key=gemini_api_key)
        
        # Set default provider
        self.default_provider = self.config['llm'].get('default_provider', 'groq')
    
    def route(self, query: str, use_groq: bool = None) -> Dict:
        """
        Route a user query to determine which resources to use.
        
        Args:
            query: User's question
            use_groq: Whether to use Groq (True) or Gemini (False). 
                     If None, uses default from config.
        
        Returns:
            Dict containing:
                - needs_rag: bool (whether to use RAG/documents)
                - needs_tool: bool (whether to call a tool)
                - tool_name: str or None (name of tool to call)
                - tool_params: dict or None (parameters for tool)
                - reasoning: str (explanation of routing decision)
                - success: bool (whether routing was successful)
        """
        
        if use_groq is None:
            use_groq = (self.default_provider == "groq")
        
        # Format routing prompt with user query
        prompt = ROUTING_PROMPT.format(query=query)
        
        try:
            # Call LLM for routing decision
            if use_groq:
                response = self._call_groq(prompt)
            else:
                response = self._call_gemini(prompt)
            
            # Parse JSON response
            routing_decision = self._parse_routing_response(response)
            
            # Validate and return
            if routing_decision:
                routing_decision['success'] = True
                return routing_decision
            else:
                # Fallback to RAG if parsing fails
                return {
                    'needs_rag': True,
                    'needs_tool': False,
                    'tool_name': None,
                    'tool_params': None,
                    'reasoning': 'Failed to parse routing decision, defaulting to RAG',
                    'success': False
                }
                
        except Exception as e:
            # Fallback to RAG on error
            return {
                'needs_rag': True,
                'needs_tool': False,
                'tool_name': None,
                'tool_params': None,
                'reasoning': f'Router error: {str(e)}, defaulting to RAG',
                'success': False,
                'error': str(e)
            }
    
    def _call_groq(self, prompt: str) -> str:
        """Call Groq LLM"""
        response = self.groq_client.chat.completions.create(
            model=self.config['llm']['groq']['model'],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Low temperature for consistent routing
            max_tokens=500
        )
        return response.choices[0].message.content
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini LLM"""
        response = self.gemini_client.models.generate_content(
            model=self.config['llm']['gemini']['model'],
            contents=prompt
        )
        return response.text
    
    def _parse_routing_response(self, response: str) -> Optional[Dict]:
        """
        Parse LLM response to extract routing decision.
        
        Expects JSON format like:
        {
            "needs_rag": true/false,
            "needs_tool": true/false,
            "tool_name": "tool_name" or null,
            "tool_params": {...} or null,
            "reasoning": "explanation"
        }
        """
        try:
            # Try to find JSON in response (LLM might add extra text)
            response = response.strip()
            
            # Find JSON block (between { and })
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx + 1]
                routing_data = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['needs_rag', 'needs_tool']
                if all(field in routing_data for field in required_fields):
                    # Ensure optional fields exist
                    routing_data.setdefault('tool_name', None)
                    routing_data.setdefault('tool_params', None)
                    routing_data.setdefault('reasoning', 'No reasoning provided')
                    
                    return routing_data
            
            return None
            
        except json.JSONDecodeError:
            return None
        except Exception:
            return None
    
    def explain_routing(self, routing_decision: Dict) -> str:
        """
        Generate human-readable explanation of routing decision.
        
        Args:
            routing_decision: Output from route() method
            
        Returns:
            Human-readable string explaining the decision
        """
        if not routing_decision.get('success', False):
            return f"Routing fallback: {routing_decision.get('reasoning', 'Unknown')}"
        
        parts = []
        
        if routing_decision['needs_rag']:
            parts.append("Searching documents")
        
        if routing_decision['needs_tool']:
            tool_name = routing_decision.get('tool_name', 'unknown')
            parts.append(f"Using tool: {tool_name}")
        
        explanation = " + ".join(parts) if parts else "No action"
        explanation += f"\nReasoning: {routing_decision['reasoning']}"
        
        return explanation