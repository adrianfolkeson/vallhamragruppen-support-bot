"""
SUPPORT STARTER AI - INTEGRATION TESTS
======================================
Tests for critical flows to ensure bot reliability

Run with: pytest tests/test_integration.py -v
Or directly: python -m tests.test_integration
"""

import os
import sys
# import pytest  # Optional - only needed for pytest runner
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot import SupportStarterBot, BotConfig, create_bot
from fault_reports import FaultReportSystem, UrgencyLevel, FaultCategory


class TestMultiTenantConfig:
    """Test multi-tenant configuration loading"""

    def test_default_config_loading(self):
        """Test that default config loads correctly"""
        config = BotConfig()
        assert config.COMPANY_NAME is not None
        assert config.phone is not None
        assert config.contact_email is not None

    def test_tenant_config_loading(self):
        """Test that tenant-specific config loads"""
        config = BotConfig(tenant_id="vallhamra")
        assert config.tenant_id == "vallhamra"
        assert config.COMPANY_NAME == "Vallhamra Gruppen AB"

    def test_missing_tenant_fallback(self):
        """Test that missing tenant config falls back to default"""
        config = BotConfig(tenant_id="nonexistent")
        assert config.tenant_id == "nonexistent"
        # Should use default values when file not found

    def test_faq_data_loading(self):
        """Test FAQ data is loaded"""
        config = BotConfig(tenant_id="vallhamra")
        assert len(config.faq_data) > 0
        assert "question" in config.faq_data[0]
        assert "answer" in config.faq_data[0]

    def test_knowledge_chunks_loading(self):
        """Test knowledge chunks are loaded"""
        config = BotConfig(tenant_id="vallhamra")
        assert len(config.knowledge_chunks) > 0
        assert "content" in config.knowledge_chunks[0]


class TestFaultReportSystem:
    """Test fault report urgency detection"""

    def setup_method(self):
        """Setup fault system for testing"""
        self.fault_system = FaultReportSystem()

    def test_critical_water_leak_detection(self):
        """Test critical water leak detection"""
        result = self.fault_system.detect_urgency("Akut! Vattenläcka i köket, det forsar vatten överallt!")
        assert result == UrgencyLevel.CRITICAL

    def test_lockout_emergency_detection(self):
        """Test lockout emergency detection"""
        result = self.fault_system.detect_urgency("Jag är låst ute! Hjälp!")
        assert result == UrgencyLevel.CRITICAL

    def test_high_urgency_no_water(self):
        """Test high urgency for no water"""
        result = self.fault_system.detect_urgency("Jag har inget vatten i kranen")
        assert result == UrgencyLevel.HIGH

    def test_high_urgency_no_heating(self):
        """Test high urgency for no heating"""
        result = self.fault_system.detect_urgency("Det är ingen värme i lägenheten")
        assert result == UrgencyLevel.HIGH

    def test_medium_urgency_dripping(self):
        """Test medium urgency for dripping"""
        result = self.fault_system.detect_urgency("Kranen droppar lite")
        assert result == UrgencyLevel.MEDIUM

    def test_water_category_detection(self):
        """Test water category detection"""
        category = self.fault_system.detect_category("Diskmaskinen läcker vatten")
        assert category == FaultCategory.WATER

    def test_electrical_category_detection(self):
        """Test electrical category detection"""
        category = self.fault_system.detect_category("Det glimmar i lampan")
        assert category == FaultCategory.ELECTRICAL

    def test_heating_category_detection(self):
        """Test heating category detection"""
        category = self.fault_system.detect_category("Elementet fungerar inte")
        assert category == FaultCategory.HEATING

    def test_fault_report_collection(self):
        """Test complete fault report collection"""
        result = self.fault_system.collect_fault_report(
            "Akut vattenläcka!",
            {"session_id": "test_123"}
        )
        assert result["report"] is not None
        assert result["response"] is not None
        assert result["report"].urgency == UrgencyLevel.CRITICAL
        assert result["escalate_immediately"] is True


class TestBotMessageProcessing:
    """Test bot message processing"""

    def setup_method(self):
        """Setup bot for testing"""
        # Use config without API key for faster testing
        os.environ["ANTHROPIC_API_KEY"] = ""
        self.bot = create_bot(anthropic_api_key="")

    def test_greeting_message(self):
        """Test simple greeting is handled"""
        response = self.bot.process_message("Hej!", "test_session_1")
        assert response.reply is not None
        assert len(response.reply) > 0
        assert response.intent in ["greeting", "llm_generated"]

    def test_contact_request(self):
        """Test contact information request"""
        response = self.bot.process_message("Vad är ert telefonnummer?", "test_session_2")
        assert response.reply is not None
        assert "0793" in response.reply or "telefon" in response.reply.lower()

    def test_fault_report_water_leak(self):
        """Test water leak fault report"""
        response = self.bot.process_message("Akut vattenläcka i köket!", "test_session_3")
        assert response.reply is not None
        # Water leak with "Akut!" triggers emergency_critical from local model
        assert response.intent in ["emergency_critical", "fault_report"]
        assert response.escalate is True

    def test_fault_report_lockout(self):
        """Test lockout fault report"""
        response = self.bot.process_message("Jag är låst ute!", "test_session_4")
        assert response.reply is not None
        # Lockout triggers lockout_emergency from local model
        assert response.intent in ["lockout_emergency", "fault_report"]
        assert response.escalate is True

    def test_general_inquiry(self):
        """Test general inquiry falls back gracefully"""
        response = self.bot.process_message("Vad ingår i hyran?", "test_session_5")
        assert response.reply is not None
        # Should handle even without API key

    def test_session_memory(self):
        """Test conversation memory across messages"""
        session_id = "test_memory_session"

        # Send first message
        response1 = self.bot.process_message(
            "Jag heter Kalle och har problem med värmen",
            session_id
        )

        # Send follow-up
        response2 = self.bot.process_message(
            "Kan du skicka en hantverkare?",
            session_id
        )

        # Both should get responses
        assert response1.reply is not None
        assert response2.reply is not None

        # Session should exist
        assert session_id in self.bot.memory.sessions


class TestRateLimiting:
    """Test rate limiting and security"""

    def setup_method(self):
        """Setup bot for testing"""
        os.environ["ANTHROPIC_API_KEY"] = ""
        self.bot = create_bot(anthropic_api_key="")

    def test_rate_limit_not_exceeded(self):
        """Test normal usage doesn't trigger rate limit"""
        for i in range(10):
            response = self.bot.process_message(f"Message {i}", "test_rate_session")
            assert response.reply is not None

    def test_security_check(self):
        """Test that security is applied"""
        # Should handle empty messages gracefully
        response = self.bot.process_message("", "test_security")
        assert response is not None


class TestLocalModelFallback:
    """Test local model handles simple queries"""

    def setup_method(self):
        """Setup for testing"""
        from local_model import LocalModel
        self.model = LocalModel()

    def test_simple_greeting(self):
        """Test simple greeting is handled locally"""
        assert self.model.can_handle("Hej!")
        result = self.model.generate("Hej!")
        assert result["response"] is not None
        assert result["intent"] == "greeting"

    def test_simple_thanks(self):
        """Test thanks is handled locally"""
        assert self.model.can_handle("Tack!")
        result = self.model.generate("Tack!")
        assert result["response"] is not None

    def test_goodbye(self):
        """Test goodbye is handled locally"""
        assert self.model.can_handle("Hejdå")
        result = self.model.generate("Hejdå")
        assert result["response"] is not None

    def test_complex_query_falls_through(self):
        """Test complex queries are NOT handled locally"""
        assert not self.model.can_handle("Vilka lägenheter har ni lediga?")


# Run tests if executed directly
if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)

    # Test classes
    test_classes = [
        ("Multi-Tenant Config", TestMultiTenantConfig),
        ("Fault Report System", TestFaultReportSystem),
        ("Bot Message Processing", TestBotMessageProcessing),
        ("Local Model Fallback", TestLocalModelFallback),
    ]

    results = {"passed": 0, "failed": 0, "errors": []}

    for name, test_class in test_classes:
        print(f"\n{'=' * 40}")
        print(f"Testing: {name}")
        print(f"{'=' * 40}")

        instance = test_class()

        # Get all test methods
        test_methods = [m for m in dir(instance) if m.startswith("test_")]

        for method_name in test_methods:
            try:
                # Setup if exists
                if hasattr(instance, "setup_method"):
                    instance.setup_method()

                # Run test
                getattr(instance, method_name)()
                print(f"  ✓ {method_name}")
                results["passed"] += 1

            except AssertionError as e:
                print(f"  ✗ {method_name}: {e}")
                results["failed"] += 1
                results["errors"].append((name, method_name, str(e)))
            except Exception as e:
                print(f"  ⚠ {method_name}: Error - {e}")
                results["failed"] += 1
                results["errors"].append((name, method_name, str(e)))

    # Summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Total:  {results['passed'] + results['failed']}")

    if results["failed"] > 0:
        print(f"\nFailed tests:")
        for suite, test, error in results["errors"]:
            print(f"  - {suite}.{test}: {error}")

    sys.exit(0 if results["failed"] == 0 else 1)
