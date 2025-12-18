from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory

# Cài đặt seed để kết quả nhận diện ngôn ngữ ổn định hơn (giống random seed)
DetectorFactory.seed = 0

def detectLanguage(text):
    """
    Hàm nhận diện ngôn ngữ sử dụng langdetect.
    Trả về mã ngôn ngữ (ví dụ: 'vi', 'en').
    """
    try:
        # langdetect trả về trực tiếp mã ngôn ngữ dạng string
        lang = detect(text)
        return lang
    except Exception as e:
        print(f"Detection error: {e}")
        # Trả về mặc định là 'en' nếu không nhận diện được (để tránh lỗi code)
        return 'en'

def translate(text, target_language='en'):
    """
    Hàm dịch văn bản sử dụng deep_translator.
    Trả về văn bản đã dịch (String).
    """
    try:
        # deep_translator trả về string kết quả luôn, không cần .text
        translator = GoogleTranslator(source='auto', target=target_language)
        translated_text = translator.translate(text)
        return translated_text
    except Exception as e:
        print(f"Translation error: {e}")
        # Trả về text gốc nếu dịch lỗi
        return text

# --- Phần chạy thử nghiệm (Test) ---
if __name__ == "__main__":
    sample_texts = [
        "Bonjour tout le monde",
        "Hola, ¿cómo estás?",
        "Hallo, wie geht's dir?",
        "Ciao, come stai?",
        "こんにちは、お元気ですか？",
        "Xin chào, bạn khỏe không?"
    ]
    
    print("--- Test Detection & Translation ---")
    for text in sample_texts:
        # Test Detect
        lang = detectLanguage(text)
        
        # Test Translate
        translated_text = translate(text, target_language='en')
        
        print(f"Original ({lang}): {text} | Translated: {translated_text}")