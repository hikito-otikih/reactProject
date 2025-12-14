from sentence_transformers import SentenceTransformer
import constant
import numpy as np

def load_CLIP_model():
    """
    load_CLIP_model is a function that loads the CLIP model.
    """
    model = SentenceTransformer(constant.CLIP_MODEL_NAME)
    return model

def embedText(model: SentenceTransformer, text: str):
    """
    embedText is a function that embeds the text.
    """
    return model.encode(text, normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)