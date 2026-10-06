import re

ALLOWED_ANIMALS = {
    "cow", "cattle", "bull", "calf", "dairy cow", "buffalo", "cat", "kitten",
    "dog", "puppy", "horse", "pony", "mare", "stallion", "livestock", "animal"
}

DISALLOWED_ANIMALS = {
    "elephant", "tiger", "lion", "bear", "shark", "whale", "pigeon", "parrot",
    "snake", "fish", "spider", "goat", "sheep", "camel"
}


def _normalize(text):
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def validate_question_with_context(question, chat_history=None):
    """Allow questions about livestock animals supported by the app.

    Returns: (is_valid: bool, reason: str)
    """
    text = _normalize(question)
    if not text:
        return False, "Please enter a veterinary or marketplace question."

    mentions_allowed = any(animal in text for animal in ALLOWED_ANIMALS)
    mentions_disallowed = any(animal in text for animal in DISALLOWED_ANIMALS)

    if mentions_disallowed and not mentions_allowed:
        return False, " LivestockAI Assistant specializes in Cows, Cats, Dogs, and Horses. Please ask questions related to these animals or livestock marketplace."

    if mentions_allowed or any(word in text for word in ["livestock", "marketplace", "animal", "care", "feed", "symptom", "disease", "price", "breed"]):
        return True, "Question is within supported animal domain."

    return False, " LivestockAI Assistant specializes in Cows, Cats, Dogs, and Horses. Please ask questions related to these animals or livestock marketplace."
