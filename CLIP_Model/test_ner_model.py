"""
Helper script to test NER model loading and entity extraction.
"""
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import os

def test_ner_model(model_path: str = "dslim/bert-base-NER"):
    """
    Test loading and using a NER model.
    
    Args:
        model_path: Path to the model (HuggingFace model ID or local path)
    """
    print(f"Attempting to load model from: {model_path}")
    
    try:
        # Check if it's a local path
        if os.path.exists(model_path) or os.path.isdir(model_path):
            print(f"Loading from local path: {model_path}")
            tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
            model = AutoModelForTokenClassification.from_pretrained(model_path, local_files_only=True)
        else:
            print(f"Loading from HuggingFace: {model_path}")
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForTokenClassification.from_pretrained(model_path)
        
        nlp = pipeline("ner", model=model, tokenizer=tokenizer)
        
        # Test with sample text
        sample_text = "Place to enjoy cultural banh mi in HCM"
        print(f"\nTesting with text: '{sample_text}'")
        
        results = nlp(sample_text)
        print(f"\nNER Results:")
        for result in results:
            print(f"  {result}")
        
        return nlp
        
    except Exception as e:
        print(f"Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Try custom model first, then fallback
    model_paths = [
        "opensource/extract_names",
        "dslim/bert-base-NER",
    ]
    
    for path in model_paths:
        print(f"\n{'='*60}")
        nlp = test_ner_model(path)
        if nlp is not None:
            print(f"\n✓ Successfully loaded model from: {path}")
            break
    else:
        print("\n✗ Failed to load any model")

