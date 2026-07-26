"""
Emotion Analyzer Module
Utilizes a specialized Hugging Face transformer model to classify 
the emotional undertone of text affecting living stakeholders (e.g. Students, Faculty).
"""

import os
from transformers import pipeline

# We use a lightweight DistilRoBERTa model fine-tuned for emotion detection.
# It classifies text into: anger, disgust, fear, joy, neutral, sadness, surprise.
MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

# Singleton pattern for the classifier to avoid reloading the model on every call
_classifier = None

def get_classifier():
    """Load the Hugging Face emotion classifier pipeline lazily."""
    global _classifier
    if _classifier is None:
        try:
            _classifier = pipeline("text-classification", model=MODEL_NAME, top_k=1)
        except Exception as e:
            print(f"Warning: Failed to load Emotion Model: {e}")
            return None
    return _classifier


def detect_emotion(text: str) -> str:
    """
    Detect the primary emotion in a given text snippet.
    
    Args:
        text (str): The text explaining the impact on a stakeholder.
        
    Returns:
        str: The dominant emotion label (e.g., 'joy', 'fear', 'anger', 'neutral'), 
             or 'neutral' if detection fails or text is too short.
    """
    if not text or len(text.strip()) < 10:
        return "neutral"
        
    classifier = get_classifier()
    if not classifier:
        return "neutral"
        
    try:
        # Truncate text for the local transformer (max 512 tokens typically)
        # 1500 chars is a safe approximation to stay under 512 tokens.
        safe_text = text[:1500] 
        result = classifier(safe_text)
        
        # Extract the highest scoring emotion
        if result and isinstance(result, list) and len(result) > 0:
            top_emotion = result[0][0]['label']
            return top_emotion
            
    except Exception as e:
        print(f"Emotion detection error: {e}")
        
    return "neutral"
