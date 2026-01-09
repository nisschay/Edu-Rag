import os
import logging
from app.utils.llm import get_llm_generator
from app.utils.embeddings import get_embedding_generator
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gemini():
    settings = get_settings()
    print(f"Using Model: {settings.GEMINI_MODEL}")
    print(f"Using Embedding Model: {settings.EMBEDDING_MODEL}")
    
    # Check if key is present (don't print full key!)
    key = settings.GEMINI_API_KEY
    if not key:
        print("ERROR: GEMINI_API_KEY is not set!")
        return
    else:
        print(f"GEMINI_API_KEY is set (starts with: {key[:4]}...)")

    try:
        # Test LLM
        print("\nTesting LLM Generation...")
        gen = get_llm_generator()
        response = gen.generate("Hello, who are you?", max_tokens=50)
        print(f"LLM Response: {response}")
        
        # Test Embeddings
        print("\nTesting Embeddings...")
        embed_gen = get_embedding_generator()
        embedding = embed_gen.embed_text("This is a test.")
        print(f"Embedding successful. Dimension: {len(embedding)}")
        
        if len(embedding) == settings.EMBEDDING_DIMENSION:
            print("Dimension matches expected config.")
        else:
            print(f"WARNING: Dimension {len(embedding)} does not match config {settings.EMBEDDING_DIMENSION}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_gemini()
