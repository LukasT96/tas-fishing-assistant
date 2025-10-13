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
from typing import List, Dict, Tuple

from src.prompts import SYSTEM_PROMPT, ROUTING_PROMPT, RAG_ANSWER_PROMPT, TOOL_INTEGRATION_PROMPT

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
    
    def query(self, question: str) -> str:
        """Main query method - processes user question"""
        
        # Search documents
        retrievals = self.search(question)
        
        if not retrievals:
            return "I don't have information about that in my knowledge base. Please check official sources."
        
        # Format context
        context = "\n\n".join([
            f"[{meta['source']}]: {doc}"
            for _, doc, meta in retrievals
        ])
        
        # Check if need to use tool (simple keyword matching for now)
        needs_tool = any(keyword in question.lower() for keyword in [
            "legal", "size", "can i keep", "is it legal", "caught", "cm"
        ])
        
        tool_result = None
        if needs_tool and self.config['tools']['legal_size_check']['enabled']:
            # Simple extraction (in production, use LLM to extract parameters)
            # For now, this is a placeholder
            tool_result = "Tool functionality to be implemented with parameter extraction"
        
        # Generate answer
        if tool_result:
            prompt = TOOL_INTEGRATION_PROMPT.format(
                query=question,
                context=context,
                tool_result=tool_result
            )
        else:
            prompt = RAG_ANSWER_PROMPT.format(
                query=question,
                context=context
            )
        
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
