"""

Router

Rounting logic to retrieve information
    - RAG only
    - RAG and Tools
    - Tools only

"""

import json
import re
from typing import Dict
from enum import Enum

from src.prompts import ROUTING_PROMPT, RAG_ANSWER_PROMPT, UI_MESSAGES, TOOL_INTEGRATION_PROMPT, TOOL_ANSWER_PROMPTS, GENERAL_CHAT_RESPONSES, GENERAL_CHAT_PROMPT

class RouteType(Enum):
    """ Types of routes that router can take """
    RAG_ONLY = "rag_only"
    TOOL_ONLY = "tool_only"
    RAG_AND_TOOL = "rag_and_tool"
    GENERAL_CHAT = "general_chat"
    
    
    
class Router:
    """
    Intelligent router that analyzes queries and determines
    which resources to use (RAG, Tools, or both)
    """
    
    
    def __init__(self, rag_model, tools_model, llm_callable):
        """ Initialize router with RAG and Tools models """
        
        self.rag = rag_model
        self.tools = tools_model
        self.llm = llm_callable
        
    
    def route(self, query: str) -> Dict:  
        return self._llm_route(query)
    
    
    def _llm_route(self, query: str) -> Dict:
        """ Use LLM to make routing decision for complex queries """
        
        prompt = ROUTING_PROMPT.format(query=query)
        
        try:
            response = self.llm(prompt)
            m = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            raw = m.group(1) if m else response

            if not raw.strip().startswith('{'):
                brace = re.search(r'\{.*\}', raw, re.DOTALL)
                raw = brace.group(0) if brace else '{}'

            decision = json.loads(raw)
            needs_rag = bool(decision.get('needs_rag'))
            needs_tool = bool(decision.get('needs_tool'))
            if needs_rag and needs_tool:
                route_type = RouteType.RAG_AND_TOOL
            elif needs_tool:
                route_type = RouteType.TOOL_ONLY
            elif needs_rag:
                route_type = RouteType.RAG_ONLY
            else:
                route_type = RouteType.GENERAL_CHAT

            return {
                'route_type': route_type,
                'needs_rag': needs_rag,
                'needs_tool': needs_tool,
                'tool_name': decision.get('tool_name'),
                'tool_params': decision.get('tool_params') or {},
                'reasoning': decision.get('reasoning', 'LLM routing decision')
            }
        except Exception as e:
            print(f"LLM routing failed: {e}, defaulting to RAG")
            return { 'route_type': RouteType.RAG_ONLY, 'needs_rag': True,
                    'needs_tool': False, 'tool_name': None, 'tool_params': {},
                    'reasoning': f'Fallback to RAG due to routing error: {e}' }
            
            
    def execute_route(self, query: str, route_decision: Dict) -> str:
        """ Execute the routing decision and generate response """
        print(f"DEBUG: Route decision: {route_decision}")
        
        route_type = route_decision['route_type']
        
        if route_type == RouteType.GENERAL_CHAT:
            return self._handle_general_chat(query)
        
        elif route_type == RouteType.RAG_ONLY:
            return self._handle_rag_only(query)
        
        elif route_type == RouteType.TOOL_ONLY:
            return self._handle_tool_only(query, route_decision)
        
        elif route_type == RouteType.RAG_AND_TOOL:
            return self._handle_rag_and_tool(query, route_decision)
        
        else:
            return UI_MESSAGES['error']
            
    
    def _handle_general_chat(self, query: str) -> str:
        """Handle casual conversation """
        query_lower = query.lower()
        
        # Quick pattern matching for common greetings
        if any(word in query_lower for word in ['hello', 'hi', 'hey']) and len(query_lower) < 20:
            return GENERAL_CHAT_RESPONSES['greeting']
        
        elif any(word in query_lower for word in ['thanks', 'thank']) and len(query_lower) < 30:
            return GENERAL_CHAT_RESPONSES['thanks']
        
        elif any(word in query_lower for word in ['bye', 'goodbye']) and len(query_lower) < 20:
            return GENERAL_CHAT_RESPONSES['goodbye']
        
        elif 'help' in query_lower and len(query_lower) < 30:
            return GENERAL_CHAT_RESPONSES['help']
        
        else:
            # Use LLM to handle complex general chat / out-of-scope queries
            prompt = GENERAL_CHAT_PROMPT.format(query=query)
            response = self.llm(prompt)
            return response
    
    
    def _handle_rag_only(self, query: str) -> str:
        """Handle queries using only RAG"""
        # Search documents
        q_norm = self.tools.normalize_text_species(query) if hasattr(self.tools, "normalize_text_species") else query
        retrievals = self.rag.search(q_norm)
        
        if not retrievals:
            return UI_MESSAGES['no_answer']
        
        # Format context
        context = "\n\n".join([
            f"[Source: {meta['source']}/{meta.get('section', 'general')}]\n{doc}"
            for _, doc, meta in retrievals
        ])
        
        # Generate answer
        prompt = RAG_ANSWER_PROMPT.format(
            query=query,
            context=context
        )
        
        answer = self.llm(prompt)
        
        # Make answer more interactive
        answer = self._enhance_answer_interactivity(answer, query)
        
        return answer

    
    def _handle_tool_only(self, query: str, route_decision: Dict) -> str:
        tool_name = route_decision['tool_name']
        params = route_decision.get('tool_params') or {}

        if tool_name == "get_fishing_weather":
            if not isinstance(params.get("location"), str):
                return UI_MESSAGES["error"]

        result = self.tools.call_tool(tool_name, **params)
        if not result.get("success"):
            # Let the model phrase the error using the code/detail
            tool_json = json.dumps(result.get("error", {}), ensure_ascii=False)
            prompt = TOOL_ANSWER_PROMPTS.format(query=query, tool_json=tool_json)
            text = self.llm(prompt)
            return self._enhance_answer_interactivity(text, query)

        tool_json = json.dumps(result["data"], ensure_ascii=False)
        prompt = TOOL_ANSWER_PROMPTS.format(query=query, tool_json=tool_json)
        text = self.llm(prompt)
        
        return self._enhance_answer_interactivity(text, query)
    
    
    def _handle_rag_and_tool(self, query: str, route_decision: Dict) -> str:
        """Handle queries using both RAG and Tools"""
        try:
            # Get RAG context
            q_norm = self.tools.normalize_text_species(query) if hasattr(self.tools, "normalize_text_species") else query
            retrievals = self.rag.search(q_norm)
            
            
            context = "\n\n".join(
                f"[Source: {m['source']}/{m.get('section', 'general')}]\n{doc}" for _, doc, m in retrievals
            ) if retrievals else "No relevant documents found."

            
            # Call tool
            tool_name = route_decision['tool_name']
            params = route_decision.get('tool_params') or {}
            result = self.tools.call_tool(tool_name, **params)

            # Extract tool data
            tool_payload = result["data"] if result.get("success") else {"error": result.get("error", {})}
            tool_json = json.dumps(tool_payload, ensure_ascii=False)

            # Generate response
            prompt = TOOL_INTEGRATION_PROMPT.format(
                query=query, 
                context=context, 
                tool_json=tool_json  # FIXED: was tool_result
            )
            text = self.llm(prompt)
            
            return self._enhance_answer_interactivity(text, query)
        
        except Exception as e:
            print(f"Error in _handle_rag_and_tool: {e}")
            import traceback
            traceback.print_exc()
            return UI_MESSAGES['error']
    
    
    def _enhance_answer_interactivity(self, answer: str, query: str) -> str:
        """ Add interactive elements to make answers more engaging """
        query_lower = query.lower()
        
        suggestions = []
        
        if 'bag limit' in query_lower or 'how many' in query_lower:
            suggestions.append("💡 Want to know size limits too?")
            suggestions.append("📍 Need good locations for this species?")
        
        elif 'where' in query_lower or 'location' in query_lower:
            suggestions.append("🌤️ Would you like the weather forecast for this location?")
            suggestions.append("🐟 Want to know what species are there?")
        
        elif 'license' in query_lower or 'permit' in query_lower:
            suggestions.append("💡 Need to know bag limits for your license type?")
            suggestions.append("📋 Want to know where to get your license?")
        
        elif any(word in query_lower for word in ['caught', 'legal', 'keep']):
            suggestions.append("📏 Want to check another fish size?")
            suggestions.append("🎣 Need to know the bag limit?")
        
        # Add suggestions if we have any
        if suggestions:
            answer += "\n\n**What else can I help with?**\n"
            answer += "\n".join(f"• {s}" for s in suggestions[:2])
        
        return answer
    
    
    def query_with_routing(self, query: str) -> str:
        """ Complete query pipeline with routing """
        route_decision = self.route(query)
        answer = self.execute_route(query, route_decision)
        
        return answer