from django import template
import re

register = template.Library()


@register.filter
def highlight(sentence, word):
    """
    Highlight the entry word in the given sentence, with support for:
    - Korean particles
    - English irregular plural forms
    - Case-insensitive matching

    Args:
        sentence (str): The sentence to return with a highlighted word.
        word (str): The base word to highlight.

    Returns:
        str: Sentence with matched words highlighted
    """
    if not word or not sentence:
        return sentence

    # Create a comprehensive regex pattern
    # For Korean: Match word followed by optional Korean particles
    # For English: Match word with various plural and particle-like endings
    korean_particles = ['은', '는', '이', '가', '을', '를', '과', '와', '에', '의']
    english_irregular_plurals = {
        'y': 'ies',  # e.g., "city" -> "cities"
        'f': 'ves',  # e.g., "leaf" -> "leaves"
        'fe': 'ves',  # e.g., "life" -> "lives"
    }

    # Generate possible word variations
    variations = [
        word,  # Original word
        word + 's',  # Simple plural
        word + 'es',  # Plural with -es
    ]

    # Add English irregular plural forms
    if word.endswith('y'):
        variations.append(word[:-1] + 'ies')
    elif word.endswith('f'):
        variations.append(word[:-1] + 'ves')
    elif word.endswith('fe'):
        variations.append(word[:-2] + 'ves')

    # Korean: Add variations with particles
    korean_variations = [
        word + particle for particle in korean_particles
    ]

    # Combine all variations
    all_variations = variations + korean_variations

    # Create a regex pattern that matches any of the variations
    pattern = r'\b(' + '|'.join(re.escape(var) for var in all_variations) + r')\b'

    # Replace the matches with the highlighted span
    highlighted_sentence = re.sub(
        pattern,
        r'<span class="highlight">\1</span>',
        sentence,
        flags=re.IGNORECASE
    )
    return highlighted_sentence