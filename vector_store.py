"""
SUPPORT STARTER AI - VECTOR STORE (ChromaDB)
==========================================
Semantic search for FAQ and knowledge chunks using ChromaDB
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from config_loader import load_config


class VectorStore:
    """
    Vector database for semantic search using ChromaDB.
    Provides much better matching than keyword search.
    """

    def __init__(self, persist_directory: str = "./data/chroma"):
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.config = None

        if CHROMADB_AVAILABLE:
            self._initialize()
        else:
            print("Warning: ChromaDB not installed. Run: pip install chromadb")

    def _initialize(self):
        """Initialize ChromaDB client and collection"""
        # Create persist directory if needed
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Load config
        self.config = load_config()

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name="knowledge_base")
        except:
            self.collection = self.client.create_collection(
                name="knowledge_base",
                metadata={"description": "FAQ and knowledge chunks for support bot"}
            )

        # Check if collection needs to be populated
        if self.collection.count() == 0:
            self._populate_from_config()

    def _populate_from_config(self):
        """Populate vector store from config FAQ and knowledge chunks"""
        if not self.config:
            return

        # Add FAQ entries
        if self.config.faq_data:
            for idx, faq in enumerate(self.config.faq_data):
                self.add_faq(
                    question=faq.get("question", ""),
                    answer=faq.get("answer", ""),
                    keywords=faq.get("keywords", []),
                    metadata={"type": "faq", "index": idx}
                )

        # Add knowledge chunks
        if self.config.knowledge_chunks:
            for idx, chunk in enumerate(self.config.knowledge_chunks):
                self.add_knowledge(
                    content=chunk.get("content", ""),
                    category=chunk.get("category", ""),
                    keywords=chunk.get("keywords", []),
                    metadata={"type": "knowledge", "id": chunk.get("id", ""), "index": idx}
                )

        print(f"Vector store populated with {self.collection.count()} documents")

    def add_faq(self, question: str, answer: str, keywords: List[str] = None, metadata: Dict = None):
        """Add a FAQ entry to the vector store"""
        if not self.collection:
            return

        # Combine question and answer for better semantic matching
        text = f"Question: {question}\nAnswer: {answer}"

        meta = metadata or {}
        meta.update({
            "type": "faq",
            "question": question,
            "answer": answer,
            "keywords": ",".join(keywords or [])
        })

        self.collection.add(
            documents=[text],
            metadatas=[meta],
            ids=[f"faq_{hash(question)}"]
        )

    def add_knowledge(self, content: str, category: str = "", keywords: List[str] = None, metadata: Dict = None):
        """Add a knowledge chunk to the vector store"""
        if not self.collection:
            return

        meta = metadata or {}
        meta.update({
            "type": "knowledge",
            "category": category,
            "keywords": ",".join(keywords or [])
        })

        self.collection.add(
            documents=[content],
            metadatas=[meta],
            ids=[f"knowledge_{hash(content)}"]
        )

    def search(self, query: str, n_results: int = 5, category: str = None) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using semantic similarity

        Args:
            query: Search query
            n_results: Number of results to return
            category: Optional category filter

        Returns:
            List of matching documents with metadata
        """
        if not self.collection:
            return []

        # Build where clause for category filtering
        where = None
        if category:
            where = {"category": category}

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )

        # Format results
        formatted = []
        if results and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                distance = results['distances'][0][i] if 'distances' in results else 0

                formatted.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": distance,
                    "similarity": 1 - distance  # Convert to similarity score
                })

        return formatted

    def search_faq(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search only FAQ entries"""
        return self.search(query, n_results=n_results, category=None)  # Filter by metadata instead

    def search_knowledge(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search only knowledge chunks"""
        return self.search(query, n_results=n_results)

    def reset(self):
        """Clear all documents from the collection"""
        if self.collection:
            self.client.delete_collection("knowledge_base")
            self.collection = self.client.create_collection(
                name="knowledge_base",
                metadata={"description": "FAQ and knowledge chunks for support bot"}
            )


# Singleton instance
_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """Get or create singleton VectorStore instance"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance


if __name__ == "__main__":
    # Test the vector store
    print("=" * 60)
    print("VECTOR STORE TEST")
    print("=" * 60)

    store = get_vector_store()

    # Test searches
    queries = [
        "hur gör jag en felanmälan",
        "vad kostar en lägenhet",
        "grannen spelar hög musik",
        "har ni lägenheter i partille"
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = store.search(query, n_results=2)
        for i, r in enumerate(results):
            print(f"  {i+1}. Similarity: {r['similarity']:.2f}")
            print(f"     Content: {r['content'][:100]}...")
