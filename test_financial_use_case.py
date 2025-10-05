#!/usr/bin/env python3
"""
Comprehensive Financial Use Case Test
Tests the personal finance application's operational integrity including LLM functionality.
"""

import requests
import json
import sys
from datetime import date, datetime
from typing import Dict, Any

# Test configuration
API_BASE = "http://127.0.0.1:8000"

class FinancialTestRunner:
    """Test runner for financial use case scenarios."""

    def __init__(self):
        self.passed_tests = 0
        self.total_tests = 0
        self.results = []

    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result."""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            print(f"✅ PASS: {name}")
        else:
            print(f"❌ FAIL: {name}")

        if details:
            print(f"   {details}")

        self.results.append({
            "test": name,
            "passed": passed,
            "details": details
        })
        print()

    def test_health_check(self):
        """Test 1: API Health Check"""
        print("=" * 60)
        print("TEST 1: API Health Check")
        print("=" * 60)
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Health Check",
                    True,
                    f"Status: {data.get('status')}, Timestamp: {data.get('timestamp')}"
                )
                return True
            else:
                self.log_test(
                    "Health Check",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except requests.exceptions.ConnectionError:
            self.log_test(
                "Health Check",
                False,
                "Cannot connect to API server. Ensure it's running on port 8000."
            )
            return False
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False

    def test_narrative_templates(self):
        """Test 2: Narrative Templates Retrieval"""
        print("=" * 60)
        print("TEST 2: Narrative Templates")
        print("=" * 60)
        try:
            response = requests.get(f"{API_BASE}/narrate/templates", timeout=5)
            if response.status_code == 200:
                data = response.json()
                templates = data.get('templates', {})
                template_names = list(templates.keys())
                self.log_test(
                    "Narrative Templates",
                    True,
                    f"Found {len(templates)} templates: {', '.join(template_names)}"
                )
                return templates
            else:
                self.log_test(
                    "Narrative Templates",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
        except Exception as e:
            self.log_test("Narrative Templates", False, str(e))
            return None

    def test_forms_available(self):
        """Test 3: Available Forms"""
        print("=" * 60)
        print("TEST 3: Available Forms")
        print("=" * 60)
        try:
            response = requests.get(f"{API_BASE}/forms/available", timeout=5)
            if response.status_code == 200:
                data = response.json()
                forms = data.get('forms', [])
                self.log_test(
                    "Forms Available",
                    True,
                    f"Found {len(forms)} form types"
                )
                return True
            else:
                self.log_test(
                    "Forms Available",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test("Forms Available", False, str(e))
            return False

    def test_llm_narration_monthly_summary(self):
        """Test 4: LLM Narration - Monthly Summary"""
        print("=" * 60)
        print("TEST 4: LLM Narration - Monthly Financial Summary")
        print("=" * 60)

        # Prepare financial data for narration
        financial_facts = {
            "month": "January 2024",
            "total_income": "$5,250.00",
            "total_expenses": "$3,847.62",
            "net_savings": "$1,402.38",
            "top_expense_category": "Housing ($2,100)",
            "second_expense_category": "Food & Dining ($625)",
            "transaction_count": 47,
            "largest_purchase": "Rent Payment - $2,100",
            "savings_rate": "26.7%"
        }

        template = """Based on the following financial data, provide a brief 2-3 sentence summary:
{facts}

Summary:"""

        try:
            response = requests.post(
                f"{API_BASE}/narrate",
                json={"template": template, "facts": financial_facts},
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                narrative_text = data.get('text', '')
                usage = data.get('usage', {})

                self.log_test(
                    "LLM Narration - Monthly Summary",
                    True,
                    f"Generated: '{narrative_text[:150]}...' (Usage: {usage})"
                )
                return narrative_text
            elif response.status_code == 503:
                self.log_test(
                    "LLM Narration - Monthly Summary",
                    False,
                    "LLM server not available (expected if Hermes is not running)"
                )
                return None
            else:
                self.log_test(
                    "LLM Narration - Monthly Summary",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
        except Exception as e:
            self.log_test("LLM Narration - Monthly Summary", False, str(e))
            return None

    def test_llm_narration_spending_insight(self):
        """Test 5: LLM Narration - Spending Insight"""
        print("=" * 60)
        print("TEST 5: LLM Narration - Spending Pattern Insight")
        print("=" * 60)

        spending_facts = {
            "category": "Food & Dining",
            "monthly_total": "$625.00",
            "transactions": 23,
            "average_per_transaction": "$27.17",
            "breakdown": "Restaurants: $425, Groceries: $200",
            "change_from_last_month": "+$85 (15.7% increase)"
        }

        template = """Analyze this spending pattern and provide a 1-2 sentence insight:
{facts}

Insight:"""

        try:
            response = requests.post(
                f"{API_BASE}/narrate",
                json={"template": template, "facts": spending_facts},
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                narrative_text = data.get('text', '')

                self.log_test(
                    "LLM Narration - Spending Insight",
                    True,
                    f"Generated: '{narrative_text[:150]}...'"
                )
                return narrative_text
            elif response.status_code == 503:
                self.log_test(
                    "LLM Narration - Spending Insight",
                    False,
                    "LLM server not available (expected if Hermes is not running)"
                )
                return None
            else:
                self.log_test(
                    "LLM Narration - Spending Insight",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
        except Exception as e:
            self.log_test("LLM Narration - Spending Insight", False, str(e))
            return None

    def test_llm_narration_budget_goal(self):
        """Test 6: LLM Narration - Budget Goal Progress"""
        print("=" * 60)
        print("TEST 6: LLM Narration - Budget Goal Progress")
        print("=" * 60)

        budget_facts = {
            "goal": "Save $15,000 for vacation",
            "current_savings": "$8,250",
            "progress": "55%",
            "months_elapsed": 5,
            "target_date": "December 2024",
            "monthly_contribution": "$1,650",
            "on_track": "Yes"
        }

        template = """Based on this budget goal progress, write a motivating 2 sentence summary:
{facts}

Progress Summary:"""

        try:
            response = requests.post(
                f"{API_BASE}/narrate",
                json={"template": template, "facts": budget_facts},
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                narrative_text = data.get('text', '')

                self.log_test(
                    "LLM Narration - Budget Goal",
                    True,
                    f"Generated: '{narrative_text}'"
                )
                return narrative_text
            elif response.status_code == 503:
                self.log_test(
                    "LLM Narration - Budget Goal",
                    False,
                    "LLM server not available (expected if Hermes is not running)"
                )
                return None
            else:
                self.log_test(
                    "LLM Narration - Budget Goal",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
        except Exception as e:
            self.log_test("LLM Narration - Budget Goal", False, str(e))
            return None

    def run_all_tests(self):
        """Run all test scenarios."""
        print("\n")
        print("🏦 FINANCIAL APPLICATION - COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print("Testing operational integrity including LLM functionality")
        print("=" * 60)
        print("\n")

        # Run tests in order
        if not self.test_health_check():
            print("\n⚠️  API server not responding. Cannot continue tests.")
            return False

        self.test_narrative_templates()
        self.test_forms_available()

        # LLM tests
        self.test_llm_narration_monthly_summary()
        self.test_llm_narration_spending_insight()
        self.test_llm_narration_budget_goal()

        # Print final summary
        self.print_summary()

        return self.passed_tests == self.total_tests

    def print_summary(self):
        """Print final test summary."""
        print("\n")
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Pass Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print("=" * 60)

        if self.passed_tests == self.total_tests:
            print("✅ ALL TESTS PASSED - Application is operational!")
        else:
            print("⚠️  Some tests failed. Check details above.")

        print("\n")
        print("📝 NOTES:")
        print("- LLM tests will fail if Hermes server is not running")
        print("- This is expected behavior - LLM features are optional")
        print("- Core API functionality should work without LLM")
        print("\n")


def main():
    """Main entry point."""
    runner = FinancialTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
