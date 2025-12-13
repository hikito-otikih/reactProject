from sentence_transformers import SentenceTransformer
import constant
def load_CLIP_model():
    """
    load_CLIP_model is a function that loads the CLIP model.
    """
    model = SentenceTransformer(constant.CLIP_MODEL_NAME)
    return model

def embedText(text: str):
    """
    embedText is a function that embeds the text.
    """
    model = load_CLIP_model()
    return model.encode(text)