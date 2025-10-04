"""
Local HTTP client for Hermes LLM (llama.cpp server).
Handles communication with local LLM for transaction narration and categorization.
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time
import os

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Response from LLM API."""
    text: str
    success: bool
    error: Optional[str] = None
    usage: Optional[Dict[str, int]] = None

class HermesClient:
    """
    HTTP client for communicating with Hermes LLM via llama.cpp server.
    Focuses on narration-only tasks, no mathematical calculations.
    """
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        """
        Initialize Hermes client.
        
        Args:
            base_url: Base URL for llama.cpp server (e.g., 'http://127.0.0.1:11434')
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv('HERMES_URL', 'http://127.0.0.1:11434')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def health_check(self) -> bool:
        """Check if the Hermes server is available."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Hermes health check failed: {e}")
            return False
    
    def generate_completion(self, 
                          prompt: str, 
                          max_tokens: int = 150,
                          temperature: float = 0.3,
                          stop_sequences: Optional[List[str]] = None) -> LLMResponse:
        """
        Generate text completion using Hermes.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
            stop_sequences: List of sequences that stop generation
            
        Returns:
            LLMResponse with generated text or error
        """
        if stop_sequences is None:
            stop_sequences = ["\n\n", "###", "---"]
            
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop": stop_sequences,
            "stream": False
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return LLMResponse(
                    text=data.get('content', '').strip(),
                    success=True,
                    usage=data.get('usage')
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Hermes API error: {error_msg}")
                return LLMResponse(
                    text="",
                    success=False,
                    error=error_msg
                )
                
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.timeout} seconds"
            logger.error(error_msg)
            return LLMResponse(text="", success=False, error=error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(text="", success=False, error=error_msg)
    
    def categorize_transaction(self, 
                             merchant: str, 
                             amount: float, 
                             description: str = "") -> LLMResponse:
        """
        Categorize a transaction using LLM.
        
        Args:
            merchant: Merchant name
            amount: Transaction amount
            description: Additional description
            
        Returns:
            LLMResponse with suggested category
        """
        from .prompts import get_categorization_prompt
        
        prompt = get_categorization_prompt(merchant, amount, description)
        
        return self.generate_completion(
            prompt=prompt,
            max_tokens=50,
            temperature=0.1,
            stop_sequences=["\n", ".", "###"]
        )
    
    def generate_narration(self, 
                          merchant: str, 
                          amount: float, 
                          category: str,
                          date: str = "",
                          description: str = "") -> LLMResponse:
        """
        Generate a natural language narration for a transaction.
        
        Args:
            merchant: Merchant name
            amount: Transaction amount
            category: Transaction category
            date: Transaction date
            description: Additional description
            
        Returns:
            LLMResponse with generated narration
        """
        from .prompts import get_narration_prompt
        
        prompt = get_narration_prompt(merchant, amount, category, date, description)
        
        return self.generate_completion(
            prompt=prompt,
            max_tokens=100,
            temperature=0.4,
            stop_sequences=["\n", "###"]
        )
    
    def suggest_merchant_cleanup(self, merchant: str) -> LLMResponse:
        """
        Suggest a cleaned-up version of a merchant name.
        
        Args:
            merchant: Raw merchant name from bank
            
        Returns:
            LLMResponse with cleaned merchant name
        """
        from .prompts import get_merchant_cleanup_prompt
        
        prompt = get_merchant_cleanup_prompt(merchant)
        
        return self.generate_completion(
            prompt=prompt,
            max_tokens=30,
            temperature=0.2,
            stop_sequences=["\n", ".", "###"]
        )
    
    def batch_categorize(self, transactions: List[Dict[str, Any]]) -> List[LLMResponse]:
        """
        Categorize multiple transactions in batch.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of LLMResponse objects with categories
        """
        results = []
        
        for transaction in transactions:
            try:
                merchant = transaction.get('merchant', '')
                amount = transaction.get('amount', 0.0)
                description = transaction.get('description', '')
                
                result = self.categorize_transaction(merchant, amount, description)
                results.append(result)
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error categorizing transaction {transaction}: {e}")
                results.append(LLMResponse(
                    text="",
                    success=False,
                    error=str(e)
                ))
        
        return results
    
    def explain_spending_pattern(self, 
                               category: str, 
                               amount: float, 
                               frequency: int,
                               period: str = "month") -> LLMResponse:
        """
        Generate explanation for spending patterns.
        
        Args:
            category: Spending category
            amount: Total amount spent
            frequency: Number of transactions
            period: Time period (month, week, etc.)
            
        Returns:
            LLMResponse with spending pattern explanation
        """
        from .prompts import get_spending_pattern_prompt
        
        prompt = get_spending_pattern_prompt(category, amount, frequency, period)
        
        return self.generate_completion(
            prompt=prompt,
            max_tokens=120,
            temperature=0.5,
            stop_sequences=["\n\n", "###"]
        )
    
    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()