"""
RAG Model - Retrieval Augmented Generation

Implementation of RAG: Retrieve information from documents (source of truth) 
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Fix tokenizer warning
import yaml
from groq import Groq
from google import genai
from dotenv import load_dotenv
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from typing import List, Dict, Tuple, Optional

from src.prompts import SYSTEM_PROMPT, ROUTING_PROMPT, RAG_ANSWER_PROMPT, TOOL_INTEGRATION_PROMPT
from src.router import Router
from src.tools_model import ToolsModel

class RAGModel:
    def __init__(self, config_path: str = "config.yml"):
        # Load env variables from .env file
        load_dotenv()
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get API keys from environment
        groq_api_key = os.getenv("GROQ_API_KEY")
        gemini_api_key = os.getenv("GOOGLE_API_KEY")

        if not groq_api_key or not gemini_api_key:
            raise ValueError("API keys not found in .env file")

        # Set default provider from config
        self.default_provider = self.config['llm'].get('default_provider', 'groq')

        # Initialize clients
        self.groq_client = Groq(api_key=groq_api_key)
        self.gemini_client = genai.Client(api_key=gemini_api_key)

        # Initialize ChromaDB
        self.chroma_client = chromadb.Client()
        self.embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=self.config['rag']['embedding']['model']
        )

        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.config['rag']['vector_db']['name'],
            embedding_function=self.embedding_function
        )
        
        # Initialize router and tools
        self.router = Router(config_path=config_path)
        self.tools = ToolsModel(config_path=config_path)
        
    
    def load_ground_truth(self, file_path: str, source_name: str = None) -> int:
        """Load a document as ground truth"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if source_name is None:
            source_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Get chunk settings from config
        chunk_size = self.config['rag']['chunk_size']
        chunk_overlap = self.config['rag']['chunk_overlap']
        
        chunks = self.chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
        self.upsert_source(chunks, source_name)
        
        return len(chunks)
    
    
    def chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunks.append(" ".join(words[i:i + chunk_size]))
            i += max(1, chunk_size - overlap)
        return chunks
    
    def upsert_source(self, chunks: List[str], source_name: str):
        """Add chunks to ChromaDB"""
        ids = [f"{source_name}:{i}" for i in range(len(chunks))]
        metas = [{"source": source_name, "chunk_id": i} for i in range(len(chunks))]
        self.collection.upsert(ids=ids, documents=chunks, metadatas=metas)

    def search(self, query: str, k: int = None) -> List[Tuple]:
        """Search for relevant chunks"""
        if k is None:
            k = self.config['rag']['top_k']
        
        r = self.collection.query(query_texts=[query], n_results=k)
        return list(zip(r["ids"][0], r["documents"][0], r["metadatas"][0]))
    
    def llm_call(self, prompt: str, use_groq: bool = None) -> str:
        """Call LLM with prompt"""
        if use_groq is None:
            use_groq = (self.default_provider == "groq")
        
        if use_groq:
            response = self.groq_client.chat.completions.create(
                model=self.config['llm']['groq']['model'],
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config['llm']['groq']['temperature'],
                max_tokens=self.config['llm']['groq']['max_tokens']
            )
            return response.choices[0].message.content
        else:
            response = self.gemini_client.models.generate_content(
                model=self.config['llm']['gemini']['model'],
                contents=prompt
            )
            return response.text
    
    def query(self, question: str, show_routing: bool = False) -> str:
        """
        Main query method - processes user question using router and tools.
        
        Args:
            question: User's question
            show_routing: Whether to include routing explanation in response
            
        Returns:
            Answer string with citations and/or tool results
        """
        
        try:
            # Step 1: Route the query
            routing_decision = self.router.route(question)
            
            context = ""
            retrievals = []
            tool_result = None
            
            # Step 2: Execute based on routing decision
            
            # 2a. Retrieve from documents if needed
            if routing_decision['needs_rag']:
                retrievals = self.search(question)
                
                if retrievals:
                    # Format context with clear citations
                    context = self._format_context_with_citations(retrievals)
                else:
                    context = "[No relevant documents found]"
            
            # 2b. Call tool if needed
            if routing_decision['needs_tool']:
                tool_name = routing_decision.get('tool_name')
                tool_params = routing_decision.get('tool_params', {})
                
                if tool_name and tool_params:
                    tool_result = self.tools.call_tool(tool_name, **tool_params)
                else:
                    tool_result = {
                        "success": False,
                        "error": "Missing tool name or parameters",
                        "message": "Could not determine which tool to use or what parameters to provide."
                    }
            
            # Step 3: Generate final answer
            answer = self._generate_answer(question, context, tool_result, routing_decision)
            
            # Optionally add routing explanation
            if show_routing:
                routing_explanation = self.router.explain_routing(routing_decision)
                answer = f"**[Routing Decision]**\n{routing_explanation}\n\n---\n\n{answer}"
            
            return answer
            
        except Exception as e:
            return f"An error occurred while processing your question.\n\n**Error:** {str(e)}\n\nPlease try rephrasing your question or contact support."
    
    def _format_context_with_citations(self, retrievals: List[Tuple]) -> str:
        """
        Format retrieved documents with clear citations.
        
        Args:
            retrievals: List of (id, document, metadata) tuples
            
        Returns:
            Formatted context string with citations
        """
        context_parts = []
        
        for idx, (doc_id, doc_text, meta) in enumerate(retrievals, 1):
            source = meta.get('source', 'Unknown')
            chunk_id = meta.get('chunk_id', '?')
            
            citation = f"[{idx}] Source: {source} (chunk {chunk_id})"
            context_parts.append(f"{citation}\n{doc_text}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str, tool_result: Optional[Dict], routing_decision: Dict) -> str:
        """
        Generate final answer based on available information.
        
        Args:
            question: User's question
            context: Retrieved document context (may be empty)
            tool_result: Tool execution result (may be None)
            routing_decision: Router's decision
            
        Returns:
            Final answer string
        """
        
        # Case 1: Both RAG and Tool
        if routing_decision['needs_rag'] and routing_decision['needs_tool'] and tool_result:
            if tool_result.get('success', False):
                tool_message = tool_result.get('message', str(tool_result))
                
                prompt = TOOL_INTEGRATION_PROMPT.format(
                    query=question,
                    context=context if context and context != "[No relevant documents found]" else "No additional context from documents.",
                    tool_result=tool_message
                )
            else:
                # Tool failed, fall back to RAG only
                prompt = RAG_ANSWER_PROMPT.format(
                    query=question,
                    context=context if context else "No relevant information found in documents."
                )
        
        # Case 2: Tool only
        elif routing_decision['needs_tool'] and tool_result:
            if tool_result.get('success', False):
                # Return tool result directly with minimal LLM processing
                tool_message = tool_result.get('message', str(tool_result))
                return tool_message
            else:
                # Tool failed
                error_msg = tool_result.get('message', 'Tool execution failed')
                return error_msg
        
        # Case 3: RAG only
        elif routing_decision['needs_rag'] and context:
            if context == "[No relevant documents found]":
                return "I don't have information about that in my knowledge base. Please check the official Inland Fisheries Service Tasmania website at https://ifs.tas.gov.au/"
            
            prompt = RAG_ANSWER_PROMPT.format(
                query=question,
                context=context
            )
        
        # Case 4: Nothing available
        else:
            return "I'm not sure how to answer that question. Could you please rephrase it or provide more details?"
        
        # Generate answer using LLM
        answer = self.llm_call(prompt)
        return answer
    
    def verify_retrieval(self, citation: str, retrievals: List[Tuple]) -> bool:
        """
        Check if citation is included in retrieved results
        """
        for _, text, _ in retrievals:
            if citation.lower() in text.lower():
                print("Citation is included in the retrieved results")
                return True
        
        print("Citation NOT found in retrieved results")
        return False
