"""
RAG Model - Retrieval Augmented Generation

Implementation of RAG: Retrieve information from documents (source of truth) 
"""

import os
import json
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Fix tokenizer warning
import yaml
from groq import Groq
from google import genai
from dotenv import load_dotenv
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from typing import List, Tuple, Dict

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
        
        
        # Initialize clients
        self.groq_client = Groq(api_key=groq_api_key)
        self.gemini_client = genai.Client(api_key=gemini_api_key)
        
        self.default_provider = self.config['llm']['default_provider']
        
        
        # Tools calling
        self.tools = ToolsModel(config_path=config_path)
        
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.Client()
        self.embedding_function = SentenceTransformerEmbeddingFunction(model_name=self.config['rag']['embedding']['model'])
        
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.config['rag']['vector_db']['name'],
            embedding_function=self.embedding_function
        )
        
    
    def load_ground_truth(self, file_path: str, source_name: str = None) -> int:
        """
        Load JSON document and prepare it for chunking
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.endswith('.json'):
            raise ValueError(f"Only JSON files are supported. Got: {file_path}")
        
        # Load JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract source name
        if source_name is None:
            source_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Get chunk settings
        chunk_size = self.config['rag']['chunk_size']
        chunk_overlap = self.config['rag']['chunk_overlap']
        
        total_chunks = 0
        
        # Process each section separately
        for section_name, section_content in data.items():
            # Convert JSON to readable text
            section_text = self._json_to_text(section_content, section_name)
            
            # Chunk the text
            chunks = self.chunk_text(section_text, chunk_size, chunk_overlap)
            
            # Upsert to vector database
            self.upsert(chunks, source_name, section_name)
            
            total_chunks += len(chunks)
        
        print(f"✅ Loaded {total_chunks} chunks from {source_name} across {len(data)} sections")
        return total_chunks
     
    
    def _json_to_text(self, content, section_name: str) -> str:
        """Helper: Convert JSON section to readable text format"""
        if isinstance(content, dict):
            lines = [f"=== {section_name.upper().replace('_', ' ')} ===\n"]
            
            for key, value in content.items():
                if isinstance(value, dict):
                    lines.append(f"\n{key.replace('_', ' ').title()}:")
                    for sub_key, sub_value in value.items():
                        lines.append(f"  • {sub_key.replace('_', ' ')}: {sub_value}")
                elif isinstance(value, list):
                    lines.append(f"\n{key.replace('_', ' ').title()}:")
                    for item in value:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                lines.append(f"  • {k.replace('_', ' ')}: {v}")
                        else:
                            lines.append(f"  • {item}")
                else:
                    lines.append(f"{key.replace('_', ' ').title()}: {value}")
            
            return "\n".join(lines)
    
    
    def chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks
        """
        words = text.split()
        chunks = []
        i = 0
        
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            i += max(1, chunk_size - overlap)
        
        return chunks
    
    
    def upsert(self, chunks: List[str], source_name: str, section_name: str):
        """
        Add chunks to ChromaDB with metadata
        """
        # Create unique IDs
        ids = [f"{source_name}:{section_name}:{i}" for i in range(len(chunks))]
        
        # Create metadata for each chunk
        metadatas = [
            {
                "source": source_name,
                "chunk_id": i,
                "section": section_name,
                "topics": self._extract_topics(chunk, section_name)
            }
            for i, chunk in enumerate(chunks)
        ]
        
        # Upsert to ChromaDB
        self.collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=metadatas
        )


    def _extract_topics(self, chunk: str, section: str) -> str:
        """Helper: Extract key topics from chunk for better filtering"""
        chunk_lower = chunk.lower()
        topics = [section]  # Always include section as primary topic
        
        # Section-specific topic extraction
        if section == 'fishing_licence':
            if 'freshwater' in chunk_lower:
                topics.append('freshwater')
            if 'saltwater' in chunk_lower or 'marine' in chunk_lower:
                topics.append('saltwater')
            if 'recreational' in chunk_lower:
                topics.append('recreational')
        
        elif section == 'species':
            species_keywords = ['trout', 'salmon', 'flathead', 'bream', 'tuna']
            topics.extend([s for s in species_keywords if s in chunk_lower])
            
            if 'bag limit' in chunk_lower:
                topics.append('bag_limit')
            if 'size limit' in chunk_lower:
                topics.append('size_limit')
        
        elif section == 'fishing_seasons':
            if 'open' in chunk_lower:
                topics.append('open_season')
            if 'closed' in chunk_lower:
                topics.append('closed_season')
        
        elif section == 'hot_fishing_spots':
            # Extract region names
            regions = ['derwent', 'east coast', 'st helens', 'bruny', 'entrecasteaux',
                    'tasman', 'flinders', 'tamar', 'devonport', 'port sorell',
                    'north west', 'king island', 'macquarie', 'hobart']
            topics.extend([r for r in regions if r in chunk_lower])
            
            # Extract location types
            location_types = ['lake', 'river', 'creek', 'dam', 'beach', 'bay', 
                            'jetty', 'wharf', 'coast', 'peninsula', 'island']
            topics.extend([loc for loc in location_types if loc in chunk_lower])
            
            # Extract species mentions in location context
            species_in_spots = ['salmon', 'flathead', 'bream', 'snapper', 'whiting', 
                            'calamari', 'squid', 'barracouta', 'kingfish']
            topics.extend([s for s in species_in_spots if s in chunk_lower])
            
            # Extract fishing methods/access
            if 'shore' in chunk_lower:
                topics.append('shore_fishing')
            if 'boat' in chunk_lower:
                topics.append('boat_fishing')
        
        return ','.join(topics)


    def search(self, query: str, k: int = None, filter_metadata: Dict = None) -> List[Tuple]:
        """
        Search for relevant chunks with optional filtering
        """
        if k is None:
            k = self.config['rag']['top_k']
        
        # Auto-detect section filter if not provided
        if filter_metadata is None:
            filter_metadata = self._create_query_filter(query)
        
        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=filter_metadata
        )
        
        # Return as list of tuples
        return list(zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0]
        ))
    
    
    def _create_query_filter(self, query: str) -> Dict:
        """Helper: Auto-detect which section to search based on query"""
        query_lower = query.lower()
        
        # License queries
        if any(word in query_lower for word in ['license', 'licence', 'permit', 'need to fish']):
            return {"section": "fishing_licence"}
        
        # Species/limit queries
        if any(word in query_lower for word in ['bag limit', 'size limit', 'legal size', 'can i keep']):
            return {"section": "species"}
        
        # Season queries
        if any(word in query_lower for word in ['season', 'when', 'open', 'closed']):
            return {"section": "fishing_seasons"}
        
        # Location queries
        if any(word in query_lower for word in ['where', 'location', 'spot', 'lake', 'river', 
                                                'beach', 'bay', 'jetty', 'fishing spot', 
                                                'good place', 'best place', 'catch at']):
            return {"section": "hot_fishing_spots"}
        
        # No filter - search all sections
        return None
    
   
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
                model=self.config['llm']['germini']['model'],
                contents=prompt
            )
            return response.text
    
    
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


