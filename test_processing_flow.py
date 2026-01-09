import time
import logging
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.file import File
from app.services import processing_service, chat_service
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_pipeline():
    db = SessionLocal()
    settings = get_settings()
    
    try:
        # 1. Create a test file record (mimic upload)
        # Assuming seed_test.py has been run and subject/unit/topic with ID 1 exists
        file_path = "/root/education_rag/README.md" # Using README as a test file
        
        test_file = File(
            id=999,
            topic_id=1,
            filename="README.md",
            filepath=file_path,
            file_type="md",
            file_size=1000,
            status="pending"
        )
        db.merge(test_file)
        db.commit()
        
        logger.info("Step 1: Created test file record")
        
        # 2. Trigger background processing
        processing_service.process_file_background(999)
        
        # 3. Check status
        # Re-open session to ensure object is persistent
        db = SessionLocal()
        test_file = db.get(File, 999)
        logger.info(f"Step 2: Processing complete. Status: {test_file.status}")
        
        if test_file.status != "ready":
             logger.error(f"Processing failed: {test_file.processing_error}")
             return

        # 4. Test Chat (Scoped)
        logger.info("Step 3: Testing scoped chat...")
        result = chat_service.chat_flexible(
            db=db,
            user_id=1,
            message="What is this project about?",
            subject_id=1,
            unit_id=1,
            topic_id=1
        )
        logger.info(f"Chat Response: {result.answer[:200]}...")
        logger.info(f"Sources: {len(result.sources)}")
        
        # 5. Test Chat (Global)
        logger.info("Step 4: Testing global chat...")
        result_global = chat_service.chat_flexible(
            db=db,
            user_id=1,
            message="Tell me about the Education RAG project.",
            subject_id=None,
            unit_id=None,
            topic_id=None
        )
        logger.info(f"Global Chat Response: {result_global.answer[:200]}...")
        logger.info(f"Global Sources: {len(result_global.sources)}")

    finally:
        # Cleanup test file and its chunks if needed
        # (Optional: keep for debug)
        db.close()

if __name__ == "__main__":
    test_full_pipeline()
