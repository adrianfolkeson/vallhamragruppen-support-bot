"""
SUPPORT STARTER AI - RAG (RETRIEVAL AUGMENTED GENERATION)
==========================================================
Knowledge base retrieval for accurate, up-to-date responses
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
from collections import Counter


@dataclass
class KnowledgeChunk:
    """A piece of knowledge from the knowledge base"""
    id: str
    content: str
    category: str
    keywords: List[str]
    priority: int = 1  # Higher = more important


@dataclass
class RetrievedContext:
    """Retrieved relevant context for a query"""
    chunks: List[KnowledgeChunk]
    query: str
    relevance_scores: List[float]
    combined_text: str


class SimpleRAG:
    """
    Simple RAG implementation using keyword matching and TF-IDF-like scoring.
    For production, consider using vector databases like Pinecone, Weaviate, or ChromaDB.
    """
    def __init__(self):
        self.knowledge_base: List[KnowledgeChunk] = []
        self.category_index: Dict[str, List[KnowledgeChunk]] = {}

    def add_knowledge(self, chunk: KnowledgeChunk) -> None:
        """Add a knowledge chunk to the knowledge base"""
        self.knowledge_base.append(chunk)

        # Index by category
        if chunk.category not in self.category_index:
            self.category_index[chunk.category] = []
        self.category_index[chunk.category].append(chunk)

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Bulk add documents from a list of dicts

        Args:
            documents: List of dicts with keys: id, content, category, keywords, priority
        """
        for i, doc in enumerate(documents):
            chunk = KnowledgeChunk(
                id=doc.get("id", f"chunk_{i}"),
                content=doc["content"],
                category=doc.get("category", "general"),
                keywords=doc.get("keywords", []),
                priority=doc.get("priority", 1)
            )
            self.add_knowledge(chunk)

    def retrieve(self, query: str, top_k: int = 3, category_filter: Optional[str] = None) -> RetrievedContext:
        """
        Retrieve relevant knowledge chunks for a query

        Args:
            query: User query
            top_k: Number of chunks to retrieve
            category_filter: Optional category filter

        Returns:
            RetrievedContext with relevant chunks
        """
        query_lower = query.lower()
        query_terms = self._extract_terms(query_lower)

        # Score chunks based on relevance
        scored_chunks = []
        candidates = self.knowledge_base

        if category_filter and category_filter in self.category_index:
            candidates = self.category_index[category_filter]

        for chunk in candidates:
            score = self._calculate_relevance(query, query_lower, query_terms, chunk)
            if score > 0:
                scored_chunks.append((chunk, score))

        # Sort by score and get top_k
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = scored_chunks[:top_k]

        # Build result
        chunks = [chunk for chunk, _ in top_chunks]
        scores = [score for _, score in top_chunks]

        # Combine text for prompt injection
        combined_text = self._format_context(chunks, scores)

        return RetrievedContext(
            chunks=chunks,
            query=query,
            relevance_scores=scores,
            combined_text=combined_text
        )

    def _extract_terms(self, text: str) -> List[str]:
        """Extract meaningful terms from text"""
        # Simple word extraction (remove punctuation, filter short words)
        words = re.findall(r'\b\w{3,}\b', text)
        return list(set(words))

    def _calculate_relevance(self, query: str, query_lower: str, query_terms: List[str],
                            chunk: KnowledgeChunk) -> float:
        """Calculate relevance score for a chunk"""
        score = 0.0

        # Exact phrase match in content
        if query_lower in chunk.content.lower():
            score += 2.0

        # Keyword matching
        for keyword in chunk.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in query_lower:
                score += 1.5

        # TF-IDF-like term frequency matching
        chunk_lower = chunk.content.lower()
        for term in query_terms:
            if term in chunk_lower:
                score += 0.3

        # Priority boost
        score *= (1 + (chunk.priority * 0.1))

        return score

    def _format_context(self, chunks: List[KnowledgeChunk], scores: List[float]) -> str:
        """Format retrieved chunks as context for prompt injection"""
        parts = []
        for i, (chunk, score) in enumerate(zip(chunks, scores), 1):
            parts.append(f"[Relevance: {score:.2f}] {chunk.content.strip()}")

        return "\n\n".join(parts)

    def get_injected_prompt(self, query: str, system_prompt: str, top_k: int = 3) -> str:
        """
        Inject retrieved context into system prompt

        Args:
            query: User query
            system_prompt: Base system prompt
            top_k: Number of chunks to retrieve

        Returns:
            Enhanced system prompt with context
        """
        context = self.retrieve(query, top_k=top_k)

        injection = f"""
## RELEVANT KNOWLEDGE BASE
The following information from the knowledge base is relevant to the user's query:

{context.combined_text}

Use ONLY this information to answer. If the information doesn't fully answer the question,
say so and offer to connect with a human.
"""
        return system_prompt + injection


class FAQManager:
    """
    Manager for FAQ-style knowledge base
    """
    def __init__(self, rag: SimpleRAG):
        self.rag = rag

    def load_faq(self, faq_list: List[Dict[str, str]]) -> None:
        """
        Load FAQ entries into the knowledge base

        Args:
            faq_list: List of dicts with 'question' and 'answer' keys
        """
        for i, faq in enumerate(faq_list):
            # Extract keywords from question
            question = faq["question"]
            keywords = self._extract_keywords(question)

            # Create formatted content
            content = f"Q: {question}\nA: {faq['answer']}"

            chunk = KnowledgeChunk(
                id=f"faq_{i}",
                content=content,
                category="faq",
                keywords=keywords,
                priority=2
            )
            self.rag.add_knowledge(chunk)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Remove common words and extract meaningful terms
        stop_words = {"är", "det", "att", "i", "på", "för", "med", "som", "och", "eller",
                     "the", "is", "a", "an", "in", "on", "for", "with", "as", "and", "or"}
        words = re.findall(r'\b\w{3,}\b', text.lower())
        return [w for w in words if w not in stop_words]

    def get_answer(self, question: str, threshold: float = 0.5) -> Optional[str]:
        """
        Get direct answer from FAQ if confidence is high enough

        Args:
            question: User question
            threshold: Minimum confidence threshold

        Returns:
            Answer if found above threshold, None otherwise
        """
        result = self.rag.retrieve(question, top_k=1)

        if result.relevance_scores and result.relevance_scores[0] >= threshold:
            # Extract just the answer part
            content = result.chunks[0].content
            if "\nA: " in content:
                return content.split("\nA: ")[1]
            return content

        return None


def create_sample_knowledge_base() -> SimpleRAG:
    """Create a sample knowledge base for testing"""
    rag = SimpleRAG()

    # Sample FAQ entries
    faq_data = [
        {
            "question": "Hur avslutar jag min prenumeration?",
            "answer": "Du kan avsluta din prenumeration när som helst genom att gå till Mina Sidor > Prenumeration > Avsluta. Uppsägningen gäller från slutet av nuvarande betalningsperiod.",
            "keywords": ["avsluta", "prenumeration", "uppsägning", "cancel", "subscription"]
        },
        {
            "question": "Vilka betalsätt accepterar ni?",
            "answer": "Vi accepterar alla större kort (Visa, Mastercard, American Express) samt Swish, faktura (via Klarna) och direktbetalning via bank.",
            "keywords": ["betalning", "kort", "swish", "faktura", "betalningsätt"]
        },
        {
            "question": "Har ni en mobilapp?",
            "answer": "Ja, vår app finns tillgänglig för både iOS (App Store) och Android (Google Play). Sök efter 'Support Starter' i din appbutik.",
            "keywords": ["app", "mobil", "ios", "android", "telefon"]
        },
        {
            "question": "Kan jag byta paket mitt under en period?",
            "answer": "Ja! Du kan uppgradera eller nedgradera när som helst. Vid uppgrdering träder den nya funktionaliteten in direkt. Vid nedgrdering får du behålla dina nuvarande funktioner till periodens slut.",
            "keywords": ["byter", "byte", "paket", "uppgradera", "nedgradera"]
        },
        {
            "question": "Hur snabbt får jag svar?",
            "answer": "Vår AI-assistent svarar omedelbart dygnet runt. För ärenden som kräver mänsklig support har vi en responstid på under 24 timmar på vardagar.",
            "keywords": ["svar", "tid", "snabbt", "response", "hjälp"]
        }
    ]

    faq_manager = FAQManager(rag)
    faq_manager.load_faq(faq_data)

    # Add pricing knowledge
    pricing_chunk = KnowledgeChunk(
        id="pricing_1",
        content="PRICING: Starter 299 kr/mån - Grundläggande support, FAQ-bot, email integration. Professional 699 kr/mån - Allt i Starter + prioriterad support, telefon, custom branding. Enterprise - Kontakta oss för offert.",
        category="pricing",
        keywords=["pris", "prislista", "kostnad", "betala", "package", "paket"],
        priority=3
    )
    rag.add_knowledge(pricing_chunk)

    # Add contact info
    contact_chunk = KnowledgeChunk(
        id="contact_1",
        content="CONTACT: Email us at support@vallhamragruppen.se or call +46 (0)8 123 45 67. Business hours: Mon-Fri 9:00-18:00 CET. For urgent matters outside hours, email urgent@vallhamragruppen.se",
        category="contact",
        keywords=["kontakt", "email", "telefon", "ring", "support", "öppettider"],
        priority=3
    )
    rag.add_knowledge(contact_chunk)

    return rag


if __name__ == "__main__":
    # Test the RAG system
    print("=" * 60)
    print("RAG SYSTEM - TEST")
    print("=" * 60)

    rag = create_sample_knowledge_base()

    test_queries = [
        "Hur avslutar jag?",
        "Vad kostar det?",
        "Finns det en app?",
        "Kontakta er"
    ]

    for query in test_queries:
        print(f"\n{'-' * 40}")
        print(f"Query: {query}")
        result = rag.retrieve(query, top_k=2)
        print(f"Retrieved context:")
        print(result.combined_text)
