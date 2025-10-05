"""
Query routing system for intelligent search strategy selection.
Routes between vector search, LLM fallback, and web search via SerpAPI.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Literal
from enum import Enum

logger = logging.getLogger(__name__)

class SearchStrategy(str, Enum):
    """Available search strategies."""
    VECTOR = "vector"
    LLM = "llm"
    WEB = "web"
    HYBRID = "hybrid"  # Combines DuckDB transactions + Qdrant documents

class QueryRouter:
    """
    Intelligent query router that selects the best search strategy.

    Routing logic:
    - VECTOR: Questions about uploaded documents (contains financial terms + personal pronouns)
    - WEB: General financial knowledge, current events, market data
    - LLM: General financial advice without specific data requirements
    """

    def __init__(self, serpapi_key: Optional[str] = None):
        self.serpapi_key = serpapi_key or os.getenv('SERPAPI_KEY')

        # Keywords that indicate document-based queries
        self.document_keywords = [
            'my', 'our', 'income', 'expense', 'deduction', 'tax', 'statement',
            'account', 'balance', 'transaction', 'payment', 'total', 'spent',
            'earned', 'saved', 'budget', 'debt', 'loan', 'investment'
        ]

        # Keywords that indicate need for transaction data (hybrid queries)
        self.transaction_keywords = [
            'total', 'sum', 'amount', 'spent', 'earned', 'balance', 'income',
            'expense', 'transaction', 'payment', 'deposit', 'withdrawal',
            'how much', 'calculate'
        ]

        # Keywords that indicate need for form/instruction guidance
        self.form_keywords = [
            'form', 'report', 'file', 'submit', 'irs', '1040', 'schedule',
            'w-2', 'w2', '1099', 'how to', 'where', 'which line', 'instructions',
            'according to', 'based on'
        ]

        # Keywords that indicate web search queries
        self.web_keywords = [
            'current', 'latest', 'today', 'now', 'recent', 'this week', 'this month',
            'stock price', 'market', 'news', 'interest rate', 'inflation',
            'mortgage rate', 'mortgage interest', 'what is the', 'how much is',
            'price of', 'cost of', 'exchange rate', 'fed rate', 'treasury',
            'dow jones', 's&p 500', 'nasdaq', 'bitcoin', 'crypto'
        ]

        # Time-sensitive indicators (highest priority for web search)
        self.time_sensitive_keywords = [
            'current', 'latest', 'today', 'now', 'recent', 'this week', 'this month',
            '2024', '2025'
        ]

    def route_query(self, question: str, has_documents: bool = True) -> Dict[str, Any]:
        """
        Determine the best search strategy for a question.

        Args:
            question: The user's question
            has_documents: Whether the user has uploaded documents

        Returns:
            Dictionary with strategy, confidence, and reasoning
        """
        question_lower = question.lower()

        # Count keyword matches
        doc_score = sum(1 for kw in self.document_keywords if kw in question_lower)
        web_score = sum(1 for kw in self.web_keywords if kw in question_lower)
        time_sensitive_score = sum(1 for kw in self.time_sensitive_keywords if kw in question_lower)
        transaction_score = sum(1 for kw in self.transaction_keywords if kw in question_lower)
        form_score = sum(1 for kw in self.form_keywords if kw in question_lower)

        # Check for personal pronouns (my, our, I)
        has_personal_reference = any(word in question_lower.split()
                                    for word in ['my', 'our', 'i', "i'm"])

        # Routing logic with priority order:
        # 0. HYBRID: Questions needing both transaction data AND form instructions
        # 1. Time-sensitive queries (current rates, prices, etc.) -> WEB (highest priority)
        # 2. Personal document queries -> VECTOR
        # 3. General web knowledge -> WEB
        # 4. General advice -> LLM

        # HIGHEST PRIORITY: Hybrid queries (transaction data + form instructions)
        if has_documents and transaction_score >= 1 and form_score >= 1 and has_personal_reference:
            return {
                "strategy": SearchStrategy.HYBRID,
                "confidence": 0.95,
                "reasoning": "Query needs both transaction data (DuckDB) and form instructions (Qdrant)",
                "fallback": SearchStrategy.VECTOR
            }

        # SECOND PRIORITY: Time-sensitive queries always go to web
        if time_sensitive_score >= 1:
            return {
                "strategy": SearchStrategy.WEB,
                "confidence": 0.95,
                "reasoning": "Time-sensitive query requiring current information",
                "fallback": SearchStrategy.LLM
            }

        # SECOND PRIORITY: Personal document queries
        if has_documents and (doc_score >= 2 or (doc_score >= 1 and has_personal_reference)):
            return {
                "strategy": SearchStrategy.VECTOR,
                "confidence": min(0.9, 0.6 + (doc_score * 0.1)),
                "reasoning": "Question appears to be about personal financial documents",
                "fallback": SearchStrategy.LLM
            }

        # THIRD PRIORITY: General web knowledge (rates, prices, comparisons)
        elif web_score >= 2:
            return {
                "strategy": SearchStrategy.WEB,
                "confidence": min(0.9, 0.7 + (web_score * 0.1)),
                "reasoning": "Question requires web search for rates, prices, or comparisons",
                "fallback": SearchStrategy.LLM
            }

        # DEFAULT: General financial advice
        else:
            return {
                "strategy": SearchStrategy.LLM,
                "confidence": 0.7,
                "reasoning": "General financial advice question",
                "fallback": None
            }

    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using SerpAPI.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search results with title, snippet, and link
        """
        if not self.serpapi_key:
            logger.warning("SerpAPI key not configured")
            return []

        try:
            from serpapi import GoogleSearch

            params = {
                "q": query,
                "api_key": self.serpapi_key,
                "num": num_results,
                "engine": "google"
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            # Extract organic results
            formatted_results = []
            for result in results.get("organic_results", [])[:num_results]:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "link": result.get("link", ""),
                    "source": "web"
                })

            logger.info(f"Found {len(formatted_results)} web results for: {query}")
            return formatted_results

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []

    def format_web_context(self, results: List[Dict[str, Any]]) -> str:
        """Format web search results as context for LLM."""
        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Web Source {i} - {result['title']}]:\n{result['snippet']}"
            )

        return "\n\n".join(context_parts)

    def extract_sources(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract source titles and links from results."""
        sources = []
        for result in results:
            if result.get('link'):
                sources.append(f"{result['title']} ({result['link']})")
            else:
                sources.append(result['title'])
        return sources
