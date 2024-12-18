import openai
import json
from openai import OpenAI
from django.conf import settings
from django.http import JsonResponse

MY_JSON = '''
{
  "word": "banana",
  "meaning": [
    {"language": "English", "meaning": "A long curved fruit which grows in clusters and has soft pulpy flesh and yellow skin when ripe."}
  ],
  "translations": [
    {"language": "Georgian", "translation": "ბანანი"},
    {"language": "Korean", "translation": "바나나"}
  ],
  "examples": [
    {"sentence": "The banana is yellow when it is ripe."},
    {"sentence": "I like to eat a banana for breakfast."},
    {"sentence": "Bananas are very nutritious and provide a quick source of energy."},
    {"sentence": "Peeling a banana is easy; you just pull back the skin."},
    {"sentence": "Despite being widely available, bananas vary greatly in flavor depending on the region they are grown in."},
    {"sentence": "The history of banana cultivation dates back thousands of years, influencing many cultures and cuisines globally."}
  ]
}
'''


def fetch_word_data_from_openai(word):
    client = OpenAI(api_key=settings.OPEN_API_KEY)

    word = 'banana'

    languages = ['Georgian', 'Korean']

    prompt = (
        f"Please provide a dictionary definition and example sentences for the word '{word}'. "
        "The definition should be in the word's original language, and translations should **only** be provided "
        f"in the following strict list of languages: {languages}. "
        "This is a strict and exhaustive list of target languages. **Do not** add or include any other languages. "
        "If a translation for a requested language is unavailable, "
        "indicate it explicitly as 'No translation available'.\n\n"
        "References:\n"
        "- For Georgian translations, use this as a reference: https://dictionary.ge/.\n"
        "- For example sentences in Korean, us e this as a reference: https://wordrow.kr/basicn/ko/meaning/.\n\n"
        "Create a total of 6 example sentences in the word's original language, "
        " ensuring they are clear, relevant, and suitable for language learners. "
        "Adjust the complexity of the sentences to match the word's difficulty. "
        "Include:\n"
        "- 2 beginner-level sentences,\n"
        "- 2 intermediate-level sentences,\n"
        "- 2 advanced-level sentences.\n\n"
        "Do not include any formatting markers like ```json or other delimiters. "
        "Create the response strictly as a valid JSON object, ready for parsing.\n\n"
        "Return the response **only** in JSON format as follows:\n\n"
        "{\n"
        '  "word": "{word}",\n'
        '  "meaning": [\n'
        '    {"language": "{language}", "meaning": "{definiton}"},\n'
        "  ],\n"
        '  "translations": [\n'
        '    {"language": "{language1}", "translation": "{translation1}"},\n'
        '    {"language": "{language2}", "translation": "{translation2}"}\n'
        "  ],\n"
        '  "examples": [\n'
        '    {"sentence": "{example1}"},\n'
        '    {"sentence": "{example2}"},\n'
        '    {"sentence": "{example3}"},\n'
        '    {"sentence": "{example4}"},\n'
        '    {"sentence": "{example5}"},\n'
        '    {"sentence": "{example6}"},\n'
        '    {"sentence": "{example7}"},\n'
        '    {"sentence": "{example8}"},\n'
        '    {"sentence": "{example9}"},\n'
        '    {"sentence": "{example10}"}\n'
        "  ]\n"
        "}"
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
    )

    content = completion.choices[0].message.content

    if content.startswith("```json"):
        content = content.lstrip("```json").rstrip("```").strip()
    print(content)

