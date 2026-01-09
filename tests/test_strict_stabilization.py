import logging
import unittest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.api.routes.chat import chat, chat_flexible_endpoint, ChatRequest
from app.models import UnitProcessingState, Unit, Subject, Topic
from app.utils.llm import LLMGenerator

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestStrictStabilization(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 1
        
    def test_chat_gating_status_not_ready(self):
        """Test that chat is blocked if status is not ready."""
        # Mock Unit with State
        unit = MagicMock()
        unit.id = 1
        state = UnitProcessingState(status="processing", chunk_count=10)
        unit.processing_state = state
        
        # Mock Service returns
        self.db.get.return_value = unit # For flexible
        # For unit_service inside chat
        with patch("app.services.unit_service.get_unit_for_subject") as mock_get_unit:
            mock_get_unit.return_value = unit
            with patch("app.services.subject_service.get_subject_for_user") as mock_get_sub:
                mock_get_sub.return_value = MagicMock() # Exist
                
                req = ChatRequest(message="Hello", unit_id=1, topic_id=1)
                
                try:
                    chat(subject_id=1, db=self.db, current_user=self.user, request=req)
                    self.fail("Should have raised HTTPException")
                except HTTPException as e:
                    self.assertEqual(e.status_code, 400)
                    self.assertIn("Material is still processing", e.detail)
                    
    def test_chat_gating_zero_chunks(self):
        """Test that chat is blocked if chunks == 0."""
        unit = MagicMock()
        unit.id = 1
        state = UnitProcessingState(status="ready", chunk_count=0) # Zero chunks!
        unit.processing_state = state
        
        with patch("app.services.unit_service.get_unit_for_subject") as mock_get_unit:
            mock_get_unit.return_value = unit
            with patch("app.services.subject_service.get_subject_for_user") as mock_get_sub:
                mock_get_sub.return_value = MagicMock()
                
                req = ChatRequest(message="Hello", unit_id=1, topic_id=1)
                try:
                    chat(subject_id=1, db=self.db, current_user=self.user, request=req)
                    self.fail("Should have raised 400 for 0 chunks")
                except HTTPException as e:
                    self.assertEqual(e.status_code, 400)
                    self.assertIn("No content available", e.detail)

    def test_chat_gating_empty_message(self):
        """Test that empty messages are blocked."""
        # Even if unit is ready
        unit = MagicMock()
        unit.processing_state = UnitProcessingState(status="ready", chunk_count=10)
        
        with patch("app.services.unit_service.get_unit_for_subject") as mock_get_unit:
            mock_get_unit.return_value = unit
            with patch("app.services.subject_service.get_subject_for_user") as mock_get_sub:
                mock_get_sub.return_value = MagicMock()
                
                req = ChatRequest(message="   ", unit_id=1) # Empty
                try:
                    chat(subject_id=1, db=self.db, current_user=self.user, request=req)
                    self.fail("Should have raised 400 for empty message")
                except HTTPException as e:
                    self.assertEqual(e.status_code, 400)
                    self.assertIn("Message cannot be empty", e.detail)

    def test_llm_rate_limiting_fallback(self):
        """Test that LLM returns 'System busy' on 429/ResourceExhausted."""
        llm = LLMGenerator(api_key="fake")
        
        # Mock internal call to raise Exception with '429'
        with patch.object(llm, '_generate_content_with_retry', side_effect=Exception("429 Resource has been exhausted (e.g. check quota)")):
            result = llm.generate("test prompt")
            self.assertEqual(result, "The system is busy. Please try again later.")

    def test_llm_general_error_fallback(self):
        """Test that LLM returns apology on generic error."""
        llm = LLMGenerator(api_key="fake")
        
        with patch.object(llm, '_generate_content_with_retry', side_effect=Exception("Random API failure")):
            result = llm.generate("test prompt")
            self.assertIn("I apologize, but I am unable to process", result)

if __name__ == "__main__":
    unittest.main()
