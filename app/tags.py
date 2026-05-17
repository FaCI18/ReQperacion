"""Auto-tag generation module for ReQperacion.

Generates relevant tags from extracted text content to improve search precision.
Tags are single words or short phrases that appear frequently in the content.
"""

import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)

# Common Spanish and English stop words to filter out
STOP_WORDS = {
    # Spanish
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "y", "e", "o", "u", "pero", "sino", "que", "de", "del",
    "en", "por", "para", "con", "sin", "sobre", "entre",
    "a", "ante", "bajo", "cabe", "contra", "desde", "hacia",
    "hasta", "mediante", "durante", "segun", "tras", "via",
    "es", "son", "era", "eran", "ser", "está", "están", "estar",
    "ha", "han", "había", "habían", "haber", "he", "has",
    "lo", "le", "les", "se", "me", "te", "nos", "os",
    "su", "sus", "mi", "mis", "tu", "tus", "nuestro", "nuestra",
    "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
    "aquel", "aquella", "aquellos", "aquellas",
    "más", "menos", "muy", "mucho", "poco", "tan", "tanto",
    "no", "si", "sí", "también", "ya", "aún", "aun",
    "como", "cuando", "donde", "porque", "aunque", "mientras",
    "todo", "toda", "todos", "todas", "algo", "nada", "cada",
    "alguien", "nadie", "cualquier", "cualquiera",
    "bien", "mal", "así", "ahora", "después", "antes", "luego",
    "aquí", "allí", "allá", "acá", "ahí",
    # English
    "the", "a", "an", "and", "or", "but", "in", "on", "at",
    "to", "for", "of", "with", "by", "from", "as", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "dare", "ought",
    "it", "its", "this", "that", "these", "those",
    "i", "you", "he", "she", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "our", "their",
    "not", "no", "so", "if", "then", "than", "too", "very",
    "just", "about", "also", "up", "out", "off", "over",
    "what", "which", "who", "whom", "when", "where", "why",
    "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "only", "own", "same",
}


def generate_tags(text: str, max_tags: int = 10) -> list[str]:
    """
    Generate relevant tags from extracted text.
    
    Strategy:
    1. Tokenize and clean text
    2. Remove stop words and short words
    3. Count word frequencies
    4. Return top N most frequent meaningful words
    
    Args:
        text: The extracted text content
        max_tags: Maximum number of tags to generate
    
    Returns:
        List of tag strings
    """
    if not text or not text.strip():
        return []

    # Clean and tokenize
    text_lower = text.lower()
    
    # Remove punctuation and numbers, keep words with letters
    words = re.findall(r'\b[a-záéíóúüñ]{3,}\b', text_lower)

    # Filter stop words
    meaningful_words = [
        word for word in words
        if word not in STOP_WORDS and len(word) >= 3
    ]

    if not meaningful_words:
        return []

    # Count frequencies
    word_counts = Counter(meaningful_words)

    # Get top N tags
    top_tags = [word for word, _ in word_counts.most_common(max_tags)]

    return top_tags
