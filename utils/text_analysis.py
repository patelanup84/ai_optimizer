# utils/text_analysis.py
import re
from typing import Dict, List, Any
import json

def analyze_brand_mentions(text: str, brand_keywords: List[str]) -> Dict[str, Any]:
    """Analyze text for brand mentions and sentiment"""
    text_lower = text.lower()
    
    # Find brand mentions
    mentions = []
    for keyword in brand_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in text_lower:
            # Find all occurrences with context
            pattern = r'.{0,50}' + re.escape(keyword_lower) + r'.{0,50}'
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                mentions.append({
                    "keyword": keyword,
                    "context": match.group(),
                    "position": match.start()
                })
    
    # Simple sentiment analysis (you could use a proper NLP library here)
    sentiment_score = calculate_sentiment(text, mentions)
    
    # Extract key themes/topics
    themes = extract_themes(text)
    
    return {
        "mentions_found": len(mentions),
        "mentions": mentions,
        "sentiment_score": sentiment_score,
        "sentiment_label": get_sentiment_label(sentiment_score),
        "themes": themes,
        "word_count": len(text.split()),
        "contains_brand": len(mentions) > 0
    }

def calculate_sentiment(text: str, mentions: List[Dict]) -> float:
    """Calculate sentiment score (-1 to 1)"""
    if not mentions:
        return 0.0
    
    # Simple keyword-based sentiment
    positive_words = ['good', 'great', 'excellent', 'amazing', 'best', 'love', 'fantastic', 
                      'wonderful', 'outstanding', 'superior', 'innovative', 'reliable']
    negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'horrible', 'poor',
                      'disappointing', 'unreliable', 'expensive', 'overpriced', 'problem']
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total_words = len(text.split())
    if total_words == 0:
        return 0.0
    
    # Normalize by text length
    sentiment = (positive_count - negative_count) / max(total_words / 10, 1)
    return max(-1.0, min(1.0, sentiment))

def get_sentiment_label(score: float) -> str:
    """Convert sentiment score to label"""
    if score > 0.2:
        return "positive"
    elif score < -0.2:
        return "negative"
    else:
        return "neutral"

def extract_themes(text: str) -> List[str]:
    """Extract key themes from text"""
    # Simple theme extraction based on common topics
    themes = []
    text_lower = text.lower()
    
    theme_keywords = {
        "product_quality": ["quality", "performance", "reliability", "durable"],
        "customer_service": ["service", "support", "help", "assistance"],
        "pricing": ["price", "cost", "expensive", "cheap", "value", "money"],
        "innovation": ["innovative", "technology", "advanced", "cutting-edge"],
        "competition": ["competitor", "alternative", "versus", "compared to"]
    }
    
    for theme, keywords in theme_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            themes.append(theme)
    
    return themes

if __name__ == "__main__":
    test_text = "Tesla makes great electric cars with excellent performance and innovative technology."
    test_keywords = ["Tesla", "electric car"]
    
    result = analyze_brand_mentions(test_text, test_keywords)
    print("Analysis result:")
    print(json.dumps(result, indent=2))
