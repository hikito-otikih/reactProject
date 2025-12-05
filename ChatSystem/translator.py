import googletrans
from googletrans import Translator


translator = Translator(service_urls=[
    'translate.google.com',
    'translate.google.co.kr',
    'translate.google.co.jp'
])

def detectLanguage(text):
    try:
        detected = translator.detect(text)
        return detected.lang
    except Exception as e:
        print(f"Detection error: {e}")
        return None

def translate(text, target_language = 'en'):
    try:
        translated = translator.translate(text, dest=target_language)
        return translated.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text
    

if __name__ == "__main__":
    sample_texts = [
        "Bonjour tout le monde",
        "Hola, ¿cómo estás?",
        "Hallo, wie geht's dir?",
        "Ciao, come stai?",
        "こんにちは、お元気ですか？"
    ]
    
    for text in sample_texts:
        translated_text = translate(text, target_language='en')
        print(f"Original: {text} | Translated: {translated_text}")