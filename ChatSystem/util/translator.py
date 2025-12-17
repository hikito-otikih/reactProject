# import googletrans
# from googletrans import Translator


# translator = Translator(service_urls=[
#     'translate.google.com',
#     'translate.google.co.kr',
#     'translate.google.co.jp'
# ])

# def detectLanguage(text):
#     try:
#         detected = translator.detect(text)
#         return detected.lang
#     except Exception as e:
#         print(f"Detection error: {e}")
#         return None

# def translate(text, target_language = 'en'):
#     try:
#         translated = translator.translate(text, dest=target_language)
#         return translated.text
#     except Exception as e:
#         print(f"Translation error: {e}")
#         return text
    

# if __name__ == "__main__":
#     sample_texts = [
#         "Bonjour tout le monde",
#         "Hola, ¿cómo estás?",
#         "Hallo, wie geht's dir?",
#         "Ciao, come stai?",
#         "こんにちは、お元気ですか？"
#     ]
    
#     for text in sample_texts:
#         translated_text = translate(text, target_language='en')
#         print(f"Original: {text} | Translated: {translated_text}")

from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory, LangDetectException
import re

# Cài đặt seed để kết quả nhận diện ngôn ngữ ổn định hơn (giống random seed)
DetectorFactory.seed = 0

def detectLanguage(text):
    """
    Detect the primary language of text, with improved handling for mixed-language content.
    Returns language code (e.g., 'vi', 'en').
    
    For tourism apps: Handles English text with Vietnamese place names gracefully.
    """
    if not text or not text.strip():
        return 'en'
    
    try:
        # Remove numbers, punctuation for better detection
        clean_text = re.sub(r'[0-9\s,\.!?\-]+', ' ', text).strip()
        
        # If text is too short or mostly non-alphabetic, default to English
        if len(clean_text) < 3:
            return 'en'
        
        # Detect language
        lang = detect(clean_text)
        
        # For mixed content, check if it's predominantly English with Vietnamese names
        # This helps avoid misdetection when English text contains Vietnamese place names
        if lang in ['vi', 'id', 'ms', 'tl']:  # Southeast Asian languages often confused
            # Count English-like words (common words, articles, prepositions)
            english_indicators = len(re.findall(
                r'\b(the|a|an|is|are|was|were|in|on|at|to|for|of|with|show|me|some|around|near|find|get|want|like|please|can|could|would|should)\b',
                text.lower()
            ))
            
            # If we find many English indicators, it's likely English with Vietnamese names
            if english_indicators >= 2:
                return 'en'
        
        return lang
        
    except LangDetectException as e:
        # If detection fails, default to English (common for very short text or mixed content)
        return 'en'
    except Exception as e:
        print(f"Detection error: {e}")
        return 'en'

def translate(text, target_language='en'):
    """
    Translate text with smart handling for proper nouns and mixed-language content.
    
    For tourism apps: Preserves Vietnamese place names when translating to English.
    Returns translated text (String).
    """
    if not text or not text.strip():
        return text
    
    try:
        # Detect source language
        source_lang = detectLanguage(text)
        
        # No translation needed if already in target language
        # This is crucial: English text with Vietnamese names should NOT be translated
        if source_lang == target_language:
            return text
        
        # Special handling for Vietnamese -> English (tourism use case)
        if source_lang == 'vi' and target_language == 'en':
            return _smart_translate_vi_to_en(text)
        
        # For English -> Vietnamese, also preserve proper nouns
        if source_lang == 'en' and target_language == 'vi':
            return _preserve_names_translate(text, source_lang, target_language)
        
        # Standard translation for other cases
        translator = GoogleTranslator(source='auto', target=target_language)
        translated_text = translator.translate(text)
        return translated_text
        
    except Exception as e:
        print(f"Translation error: {e}")
        # Return original text on error
        return text

def _preserve_names_translate(text, source_lang, target_lang):
    """
    Translate while preserving capitalized proper nouns (names, places).
    Used for any language pair where we want to keep names intact.
    """
    try:
        # Match capitalized words/phrases (likely proper nouns)
        proper_noun_pattern = r'\b([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ][a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]+(?:\s+[A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ][a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]*)*)\b'
        
        proper_nouns = re.findall(proper_noun_pattern, text)
        
        if not proper_nouns:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            return translator.translate(text)
        
        # Create placeholders
        placeholder_map = {}
        temp_text = text
        proper_nouns.sort(key=len, reverse=True)
        
        for i, noun in enumerate(proper_nouns):
            placeholder = f"NAMEPLACEHOLDER{i}HERE"
            placeholder_map[placeholder] = noun
            temp_text = re.sub(r'\b' + re.escape(noun) + r'\b', placeholder, temp_text)
        
        # Translate
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated = translator.translate(temp_text)
        
        # Restore names
        for placeholder, original in placeholder_map.items():
            translated = translated.replace(placeholder, original)
        
        return translated
        
    except Exception as e:
        print(f"Name preservation error: {e}")
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return translator.translate(text)

def _smart_translate_vi_to_en(text):
    """
    Smart Vietnamese to English translation that preserves proper nouns.
    
    Strategy:
    1. Identify potential proper nouns (capitalized words, Vietnamese names, places)
    2. Replace them with unique placeholders
    3. Translate the rest
    4. Restore the proper nouns exactly as they were
    """
    try:
        # Extended pattern to match Vietnamese proper nouns and place names
        # Matches: Capitalized words with Vietnamese characters, multi-word names
        # Examples: "Quận 1", "Bến Thành", "Phố Đi Bộ Nguyễn Huệ", "Nhà Thờ Đức Bà"
        patterns = [
            # Multi-word capitalized phrases (e.g., "Bến Thành Market", "Phố Đi Bộ")
            r'\b([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ][a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]+(?:\s+[A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ]?[a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]+)+)\b',
            # Vietnamese place patterns with numbers (e.g., "Quận 1", "District 1")
            r'\b(Quận|Huyện|Phường|Đường|District)\s+\d+\b',
            # Single capitalized Vietnamese words
            r'\b([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ][a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]*)\b'
        ]
        
        # Collect all proper nouns (use set to avoid duplicates, then list to maintain order)
        proper_nouns = []
        seen = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Handle tuple results from regex groups
                noun = match if isinstance(match, str) else match[0] if match else ""
                if noun and noun not in seen and len(noun) > 1:
                    # Skip common Vietnamese words that shouldn't be preserved
                    skip_words = {'Tôi', 'Bạn', 'Của', 'Với', 'Trong', 'Ngoài', 'Trên', 'Dưới'}
                    if noun not in skip_words:
                        proper_nouns.append(noun)
                        seen.add(noun)
        
        # If no proper nouns found, just translate normally
        if not proper_nouns:
            translator = GoogleTranslator(source='vi', target='en')
            return translator.translate(text)
        
        # Create placeholder mapping with unique, translation-resistant placeholders
        placeholder_map = {}
        temp_text = text
        
        # Sort by length (longest first) to avoid partial replacements
        proper_nouns.sort(key=len, reverse=True)
        
        for i, noun in enumerate(proper_nouns):
            # Use UPPERCASE placeholder with numbers (less likely to be translated)
            placeholder = f"PROPERNOUNJJJ{i}JJJPLACEHOLDER"
            placeholder_map[placeholder] = noun
            # Use word boundaries to avoid partial matches
            temp_text = re.sub(r'\b' + re.escape(noun) + r'\b', placeholder, temp_text)
        
        # Translate text with placeholders
        translator = GoogleTranslator(source='vi', target='en')
        translated = translator.translate(temp_text)
        
        # Restore proper nouns exactly as they were
        for placeholder, original in placeholder_map.items():
            translated = translated.replace(placeholder, original)
        
        return translated
        
    except Exception as e:
        print(f"Smart translation error: {e}, falling back to standard translation")
        # Fallback to standard translation
        translator = GoogleTranslator(source='vi', target='en')
        return translator.translate(text)

# --- Test Examples ---
if __name__ == "__main__":
    print("=" * 90)
    print("TOURISM APP TRANSLATOR TEST - Vietnamese Names Preservation")
    print("=" * 90)
    
    test_cases = [
        # Pure foreign languages
        ("Bonjour tout le monde", "Should translate from French"),
        ("Hola, ¿cómo estás?", "Should translate from Spanish"),
        
        # Pure Vietnamese (should translate but preserve place names)
        ("Xin chào, bạn khỏe không?", "Pure Vietnamese greeting"),
        ("Tôi muốn đi tham quan Quận 1", "Vietnamese with place name 'Quận 1'"),
        ("Cho tôi xem nhà hàng ở Bến Thành", "Vietnamese with 'Bến Thành'"),
        
        # English with Vietnamese place names (MOST IMPORTANT - should NOT translate)
        ("Show me some restaurants in Quận 1", "English + Vietnamese place"),
        ("I want to visit Bến Thành Market", "English + Vietnamese name"),
        ("Where is Phố Đi Bộ Nguyễn Huệ?", "English + full Vietnamese place name"),
        ("Find hotels near Nhà Thờ Đức Bà", "English + Vietnamese landmark"),
        ("Show me schools around District 1", "English only"),
        
        # Mixed Vietnamese-English
        ("Tôi muốn đi shopping ở District 1", "Vietnamese + English word"),
        
        # Short/ambiguous text
        ("museum", "English category word"),
        ("district 1", "English place"),
        ("shopping area", "English phrase"),
        ("5", "Number only"),
        
        # Real user examples from the bug
        ("school", "Single English word"),
    ]
    
    print("\n{:<50} {:<12} {:<8} {}".format("INPUT TEXT", "DETECTED", "CHANGED", "ENGLISH OUTPUT"))
    print("-" * 90)
    
    for text, description in test_cases:
        detected_lang = detectLanguage(text)
        translated = translate(text, target_language='en')
        
        # Check if translation occurred
        changed = "YES" if text != translated else "NO"
        changed_marker = "✓" if text != translated else "○"
        
        print(f"{text:<50} {detected_lang:>2} {changed_marker:>6}   {translated}")
    
    print("\n" + "=" * 90)
    print("KEY: ○ = No translation (already English or preserved)")
    print("     ✓ = Translated (but Vietnamese names should be preserved)")
    print("=" * 90)
