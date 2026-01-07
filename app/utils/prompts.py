"""
Prompt templates for LLM interactions.

This module contains all prompt templates used in the system:
- Summarization prompts (topic, unit)
- Intent classification prompts
- Chat/RAG prompts for different intents
"""

from typing import Literal


# =============================================================================
# SUMMARIZATION PROMPTS
# =============================================================================

TOPIC_SUMMARY_PROMPT = """You are an educational content summarizer. Create a concise summary of the following academic content.

TOPIC: {topic_title}
SUBJECT: {subject_name}
UNIT: {unit_title}

CONTENT:
{chunks_text}

INSTRUCTIONS:
1. Create a concept-focused summary (200-300 tokens)
2. Focus on key concepts, definitions, and important relationships
3. Use clear, educational language
4. Do NOT include examples unless they are essential
5. Do NOT add information not present in the content
6. Structure the summary logically

SUMMARY:"""


UNIT_SUMMARY_PROMPT = """You are an educational content summarizer. Create a structured summary of a teaching unit from its topic summaries.

UNIT: {unit_title}
SUBJECT: {subject_name}

TOPIC SUMMARIES:
{topic_summaries_text}

INSTRUCTIONS:
1. Create a comprehensive unit summary (300-500 tokens)
2. Structure content in logical teaching order
3. Show how topics connect and build upon each other
4. Highlight the main learning objectives
5. Do NOT add information not present in the topic summaries
6. Make it suitable for a student reviewing the unit

UNIT SUMMARY:"""


# =============================================================================
# INTENT CLASSIFICATION PROMPTS
# =============================================================================

INTENT_CLASSIFICATION_PROMPT = """Classify the user's educational query intent.

CONTEXT:
- Subject: {subject_name}
- Unit: {unit_title}
- Topic: {topic_title}

USER MESSAGE: {message}

INTENT OPTIONS:
1. teach_from_start - User wants to learn the topic/unit from the beginning
2. explain_topic - User wants an overview or explanation of a specific topic
3. explain_detail - User wants detailed explanation of a specific concept
4. revise - User wants to review/revise previously learned material
5. generate_questions - User wants practice questions or exercises

Respond with ONLY the intent name (e.g., "explain_detail"):"""


# =============================================================================
# CHAT/RAG PROMPTS BY INTENT
# =============================================================================

TEACH_FROM_START_PROMPT = """You are an educational tutor teaching a student from the beginning.

CONTEXT:
- Subject: {subject_name}
- Unit: {unit_title}

UNIT OVERVIEW:
{context}

STUDENT'S REQUEST: {message}

INSTRUCTIONS:
1. Teach the material step by step, as if the student is new
2. Start with foundational concepts before moving to complex ones
3. Use clear, educational language
4. ONLY use information from the provided context
5. If the information is not in the context, say "This information is not in your uploaded material"
6. Be encouraging and supportive

RESPONSE:"""


EXPLAIN_TOPIC_PROMPT = """You are an educational tutor explaining a topic.

CONTEXT:
- Subject: {subject_name}
- Unit: {unit_title}
- Topic: {topic_title}

TOPIC SUMMARY:
{summary_context}

DETAILED CONTENT:
{chunk_context}

STUDENT'S QUESTION: {message}

INSTRUCTIONS:
1. Provide a clear, comprehensive explanation of the topic
2. Use the summary for overview and chunks for details
3. ONLY use information from the provided context
4. If the information is not in the context, say "This information is not in your uploaded material"
5. Structure your response logically

RESPONSE:"""


EXPLAIN_DETAIL_PROMPT = """You are an educational tutor explaining a specific concept in detail.

CONTEXT:
- Subject: {subject_name}
- Unit: {unit_title}
- Topic: {topic_title}

RELEVANT CONTENT:
{context}

STUDENT'S QUESTION: {message}

INSTRUCTIONS:
1. Provide a detailed, step-by-step explanation
2. Focus on the specific concept the student is asking about
3. ONLY use information from the provided context
4. If the information is not in the context, say "This information is not in your uploaded material"
5. Be thorough but clear

RESPONSE:"""


REVISE_PROMPT = """You are an educational tutor helping a student revise.

CONTEXT:
- Subject: {subject_name}
- Unit: {unit_title}

UNIT SUMMARY:
{context}

STUDENT'S REQUEST: {message}

INSTRUCTIONS:
1. Help the student review the key concepts
2. Highlight important points they should remember
3. ONLY use information from the provided context
4. If the information is not in the context, say "This information is not in your uploaded material"
5. Be concise but comprehensive

RESPONSE:"""


GENERATE_QUESTIONS_PROMPT = """You are an educational tutor creating practice questions.

CONTEXT:
- Subject: {subject_name}
- Unit: {unit_title}
- Topic: {topic_title}

CONTENT FOR QUESTIONS:
{context}

STUDENT'S REQUEST: {message}

INSTRUCTIONS:
1. Generate practice questions based ONLY on the provided content
2. Include a mix of question types (conceptual, application, etc.)
3. Provide brief answers or answer guidelines
4. If there's not enough content for questions, say "Not enough content to generate meaningful questions"
5. Questions should test understanding, not memorization

RESPONSE:"""


NOT_FOUND_RESPONSE = "This information is not found in your uploaded material. Please upload relevant content or ask about topics that are in your materials."


def get_intent_prompt() -> str:
    """Get the intent classification prompt template."""
    return INTENT_CLASSIFICATION_PROMPT


def get_chat_prompt(intent: str) -> str:
    """
    Get the appropriate chat prompt template for an intent.
    
    Args:
        intent: The classified intent.
        
    Returns:
        Prompt template string.
    """
    prompts = {
        "teach_from_start": TEACH_FROM_START_PROMPT,
        "explain_topic": EXPLAIN_TOPIC_PROMPT,
        "explain_detail": EXPLAIN_DETAIL_PROMPT,
        "revise": REVISE_PROMPT,
        "generate_questions": GENERATE_QUESTIONS_PROMPT,
    }
    
    return prompts.get(intent, EXPLAIN_DETAIL_PROMPT)


def get_topic_summary_prompt() -> str:
    """Get the topic summary prompt template."""
    return TOPIC_SUMMARY_PROMPT


def get_unit_summary_prompt() -> str:
    """Get the unit summary prompt template."""
    return UNIT_SUMMARY_PROMPT
