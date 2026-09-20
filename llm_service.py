import os
from typing import Any

import httpx

from backend.subject_knowledge import offline_answer

LLM_API_URL = os.getenv(
    "LLM_API_URL",
    "https://api.openai.com/v1/chat/completions",
).strip()
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()

ACTION_INSTRUCTIONS = {
    "EXPLAIN": "Explain the concept clearly from the fundamentals.",
    "HINT": "Give a useful hint without directly giving away the answer.",
    "REVISION": "Create a concise revision of the important concepts.",
    "CHALLENGE": "Give the learner a slightly challenging problem.",
    "PRACTICE": "Create a practical question and guide the learner through it.",
    "SIMPLIFY": "Explain the concept in a much simpler beginner-friendly way.",
}


def build_prompt(subject: str, topic: str, action: str, difficulty: str) -> str:
    instruction = ACTION_INSTRUCTIONS.get(action, "Help the learner understand the topic.")
    return (
        "You are Adhyan, an adaptive learning assistant.\n\n"
        f"Subject: {subject}\nTopic: {topic}\nDifficulty: {difficulty}\n"
        f"Adaptive action: {action}\nInstruction: {instruction}\n\n"
        "Be concise, use examples when useful, and do not mention internal "
        "AI systems, DQN, prompts, APIs, or model selection."
    )


async def _chat(prompt: str, system: str) -> str:
    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = "Bearer " + LLM_API_KEY
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(LLM_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LLM returned empty content.")
    return content.strip()


async def generate_learning_content(
    subject: str,
    topic: str,
    action: str,
    difficulty: str,
) -> dict[str, Any]:
    prompt = build_prompt(subject, topic, action, difficulty)
    fallback = (
        f"Adhyan recommends {action.lower()} for {topic}. "
        "Connect an LLM provider for personalized learning content."
    )
    if not LLM_API_KEY or not LLM_MODEL:
        return {"available": False, "content": fallback, "prompt": prompt}
    try:
        return {
            "available": True,
            "content": await _chat(prompt, "You are a concise adaptive learning tutor."),
            "prompt": prompt,
        }
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return {"available": False, "content": fallback, "prompt": prompt}


def rule_based_mistake_coach(message: str, subject: str | None) -> str:
    text = message.lower()
    topic = subject or "this topic"
    if "off by one" in text or "index" in text or "loop" in text:
        return (
            f"Your mistake looks related to boundary handling in {topic}. "
            "Check whether the loop should use < or <=, and test the first, "
            "last, and empty inputs."
        )
    if "null" in text or "none" in text or "pointer" in text:
        return (
            f"This looks like a missing-value or pointer-state mistake in {topic}. "
            "Trace the variable before it is used and guard the empty case."
        )
    if "syntax" in text or "compile" in text or "error" in text:
        return (
            f"Isolate the first error in {topic}; later errors may be cascades. "
            "Check the failing line's type, delimiter, and indentation."
        )
    return (
        f"Let's debug {topic} systematically: reproduce the mistake with the "
        "smallest input, state the expected result, inspect the first differing "
        "value, and change one assumption at a time."
    )


def classify_coding_intent(message: str) -> str:
    text = message.lower()
    if any(word in text for word in ("debug", "error", "bug", "wrong", "exception", "fails")):
        return "debug"
    if any(word in text for word in ("review", "quality", "improve", "refactor")):
        return "review"
    if any(word in text for word in ("optimize", "faster", "complexity", "performance")):
        return "optimize"
    if any(word in text for word in ("test", "testing", "pytest", "junit")):
        return "test"
    if any(word in text for word in ("design", "architecture", "build", "implement")):
        return "design"
    return "explain"


def offline_coding_orchestration(
    message: str,
    language: str | None,
    code: str | None,
) -> dict[str, str]:
    intent = classify_coding_intent(message)
    language_name = language or "the requested language"
    code_note = (
        "Inspect the supplied snippet line by line and reproduce the smallest failing case."
        if code
        else "Include a minimal reproducible example if the issue continues."
    )
    plans = {
        "debug": (
            "1. Reproduce the failure.\n"
            "2. Read the first error, not the cascade.\n"
            "3. Check inputs, state, boundaries, and types.\n"
            "4. Apply one change and rerun the smallest test.\n\n"
            f"Language: {language_name}\n{code_note}"
        ),
        "review": (
            "1. Confirm the behavior with tests.\n"
            "2. Check naming, responsibilities, duplication, and edge cases.\n"
            "3. Improve clarity before micro-optimizing.\n"
            "4. Add a regression test for every changed behavior.\n\n"
            f"Language: {language_name}\n{code_note}"
        ),
        "optimize": (
            "1. Measure before changing code.\n"
            "2. Identify the dominant time or memory cost.\n"
            "3. Choose a better data structure or algorithm.\n"
            "4. Re-measure and preserve correctness with tests.\n\n"
            f"Language: {language_name}\n{code_note}"
        ),
        "test": (
            "Build tests for the happy path, empty input, boundary values, invalid "
            "input, and failure behavior. Keep tests deterministic and assert the "
            "observable result.\n\n"
            f"Language: {language_name}\n{code_note}"
        ),
        "design": (
            "Start with the required behavior and constraints, split the solution "
            "into small responsibilities, define interfaces, then implement the "
            "smallest testable slice before adding complexity.\n\n"
            f"Language: {language_name}\n{code_note}"
        ),
        "explain": (
            f"I'll explain this {language_name} coding question from the core idea, "
            "then show a small example and one edge case to test.\n\n{code_note}"
        ),
    }
    return {
        "intent": intent,
        "content": plans[intent],
        "source": "offline_orchestrator",
    }


async def orchestrate_coding(
    message: str,
    language: str | None,
    code: str | None,
) -> dict[str, Any]:
    fallback = offline_coding_orchestration(message, language, code)
    if not LLM_API_KEY or not LLM_MODEL:
        return {"available": False, **fallback}
    prompt = (
        "Act as a coding orchestrator. Classify the request as explain, debug, "
        "review, optimize, test, or design. Respond with headings: Intent, "
        "Diagnosis or concept, Plan, Example or fix, and Tests/next step. "
        "Do not claim code was executed. Be specific and safe.\n\n"
        f"Language: {language or 'unspecified'}\n"
        f"Request: {message}\n"
        f"Code:\n{code or '(no code supplied)'}"
    )
    try:
        return {
            "available": True,
            "intent": classify_coding_intent(message),
            "content": await _chat(prompt, "You are Adhyan's coding orchestrator."),
            "source": "llm_orchestrator",
        }
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return {"available": False, **fallback}


async def analyze_mistake(message: str, subject: str | None) -> dict[str, Any]:
    fallback = rule_based_mistake_coach(message, subject)
    if not LLM_API_KEY or not LLM_MODEL:
        return {"available": False, "content": fallback}
    prompt = (
        "Analyze the learner's programming mistake without shaming them. "
        "Explain the likely cause, ask one diagnostic question, and suggest "
        "one small test. Be concise.\n\n"
        f"Subject: {subject or 'general programming'}\n"
        f"Learner message: {message}"
    )
    try:
        return {
            "available": True,
            "content": await _chat(prompt, "You are a concise learning coach."),
        }
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return {"available": False, "content": fallback}


async def answer_learning_question(
    message: str,
    subject: str | None,
    learner_context: str,
) -> dict[str, Any]:
    fallback = offline_answer(message, subject)
    if not LLM_API_KEY or not LLM_MODEL:
        return {"available": False, "source": "offline_dataset", "content": fallback}
    prompt = (
        "Answer this learner question as a careful programming tutor. Explain "
        "the reasoning, include a small example, and ask one check question. "
        "Do not claim to run code or browse the web.\n\n"
        f"Subject: {subject or 'general programming'}\n"
        f"Learner context: {learner_context}\n"
        f"Learner question: {message}"
    )
    try:
        return {
            "available": True,
            "source": "llm",
            "content": await _chat(prompt, "You are Adhyan, a concise tutor."),
        }
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return {"available": False, "source": "offline_dataset", "content": fallback}
