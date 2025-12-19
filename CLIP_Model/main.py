from typing import List, Dict, Any, Optional
import constant
import sqlite3
import json
import numpy as np
import faiss
import time
import pickle
import os
from sentence_transformers import SentenceTransformer
from sentence_transformers import util as TransformerUtil
import spacy
from rapidfuzz import fuzz
import unicodedata

from init_model import embedText, load_CLIP_model
from loadFaiss import loadEmbeddingData
# # from AggregateScore import computeScore
# from util import imageIdsToPlaceIdsAndUrls
from AggregateScore import buildFaiss, findBestMatch

from util import printBestMatchUtility, timing
## Neu la max thi search tren index cua do
## Neu la weighted thi phai gop score cua tung anh vao, tao faiss index moi roi moi search

## 
def preload():
    global model, index, grouped_images, ner_model, ner_data, spacy_ner_model, places_names_data

    model = load_CLIP_model()
    index, grouped_images = loadEmbeddingData()
    
    # Load NER model and data (sentence transformer for semantic search)
    ner_model = SentenceTransformer("paraphrase-mpnet-base-v2")
    ner_data_path = os.path.join("model_testing", "arrays.pkl")
    if os.path.exists(ner_data_path):
        with open(ner_data_path, 'rb') as f:
            ner_data = pickle.load(f)
    else:
        ner_data = None
        print(f"Warning: NER data file not found at {ner_data_path}")
    
    # Load spaCy NER model for entity extraction
    try:
        spacy_ner_model = spacy.load("xx_ent_wiki_sm")
        print("spaCy NER model (xx_ent_wiki_sm) loaded successfully")
    except Exception as e:
        spacy_ner_model = None
        print(f"Warning: spaCy NER model could not be loaded: {e}")
        print("You may need to install it with: python -m spacy download xx_ent_wiki_sm")
    
    # Load places names data for fuzzy matching
    places_names_data = load_places_names_data()

def computeCLIPScores(text_embedding: np.ndarray, grouped_images: Dict[int, List[Dict[str, Any]]], mode: str = 'max', **kwargs) -> Dict[int, float]:
    """
    Compute CLIP scores per place_id.
    Returns a dictionary with keys (place_id) and values (score).
    """
    clip_scores = {}
    
    if mode == 'max':
        # For max mode, find the maximum similarity score among all images for each place
        for place_id, imagesData in grouped_images.items():
            max_score = -np.inf
            for imageData in imagesData:
                embedding = imageData["embedding"]
                # Reshape to 2D for cos_sim: (1, dim) and (1, dim)
                score = TransformerUtil.cos_sim(
                    text_embedding.reshape(1, -1), 
                    embedding.reshape(1, -1)
                ).item()
                max_score = max(max_score, score)
            clip_scores[place_id] = max_score
    
    elif mode == 'weighted':
        # For weighted mode, compute weighted average of embeddings then similarity
        mainImageWeight = kwargs.get("weight", 1.5)
        for place_id, imagesData in grouped_images.items():
            embeddingList = [imageData["embedding"] for imageData in imagesData]
            weights = [mainImageWeight if imageData["isMainImage"] else 1 for imageData in imagesData]
            sum_weights = sum(weights)
            weights = [w / sum_weights for w in weights]
            overallEmbedding = np.sum([emb * w for emb, w in zip(embeddingList, weights)], axis=0).astype(np.float32)
            # Reshape to 2D for cos_sim
            score = TransformerUtil.cos_sim(
                overallEmbedding.reshape(1, -1), 
                text_embedding.reshape(1, -1)
            ).item()
            clip_scores[place_id] = score
    
    elif mode == 'mean':
        # For mean mode, compute mean similarity score
        for place_id, imagesData in grouped_images.items():
            scores = []
            for imageData in imagesData:
                embedding = imageData["embedding"]
                # Reshape to 2D for cos_sim
                score = TransformerUtil.cos_sim(
                    text_embedding.reshape(1, -1), 
                    embedding.reshape(1, -1)
                ).item()
                scores.append(score)
            clip_scores[place_id] = np.mean(scores).item()
    
    else:
        raise ValueError(f"Invalid mode: {mode}")
    
    return clip_scores

def remove_tone_marks(text: str) -> str:
    """
    Remove Vietnamese tone marks (diacritics) from text.
    """
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    text = unicodedata.normalize('NFC', text)
    return text

def extract_entities(description: str, nlp_model) -> List[str]:
    """
    Extract named entities (PERSON, ORG, LOC, etc.) from description using spaCy NER model.
    Returns a list of entity text strings.
    """
    if nlp_model is None:
        return []
    
    try:
        doc = nlp_model(description)
        # Extract all named entities
        entities = [ent.text.strip() for ent in doc.ents if ent.text.strip()]
        # Filter out very short entities and return unique ones
        entities = [e for e in entities if len(e) > 1]
        return list(set(entities))  # Return unique entities
    except Exception as e:
        print(f"Error extracting entities: {e}")
        return []

def load_places_names_data(db_path: str = "places_names.db", table_name: str = "places_names") -> Optional[Dict[int, Dict[str, str]]]:
    """
    Load places names data from the temp database.
    Returns a dictionary: {place_id: {'title': ..., 'title_no_tone': ..., 'address': ..., 'address_no_tone': ...}}
    """
    if not os.path.exists(db_path):
        print(f"Warning: Places names database not found at {db_path}. Run build_places_names.py first.")
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT place_id, title, title_no_tone, address, address_no_tone FROM {table_name}")
    results = cursor.fetchall()
    conn.close()
    
    places_data = {}
    for place_id, title, title_no_tone, address, address_no_tone in results:
        places_data[place_id] = {
            'title': title or "",
            'title_no_tone': title_no_tone or "",
            'address': address or "",
            'address_no_tone': address_no_tone or ""
        }
    
    print(f"Loaded {len(places_data)} places names from database")
    return places_data

def computeFuzzyScores(description: str, entities: List[str], places_names_data: Dict[int, Dict[str, str]], 
                       token_set_weight: float = 0.5, partial_ratio_weight: float = 0.5) -> Dict[int, float]:
    """
    Compute fuzzy matching scores per place_id by comparing extracted entities
    with place titles and addresses.
    
    Args:
        description: Original query description
        entities: List of extracted entities from NER
        places_names_data: Dictionary of place names data
        token_set_weight: Weight for token_set_ratio (default 0.5)
        partial_ratio_weight: Weight for partial_ratio (default 0.5)
    
    Returns:
        Dictionary mapping place_id to fuzzy match score (0-100)
    """
    if not places_names_data or not entities:
        return {}
    
    # Remove tone marks from description and entities for better matching
    description_no_tone = remove_tone_marks(description)
    entities_no_tone = [remove_tone_marks(e) for e in entities]
    
    fuzzy_scores = {}
    
    for place_id, place_data in places_names_data.items():
        title = place_data['title']
        title_no_tone = place_data['title_no_tone']
        address = place_data['address']
        address_no_tone = place_data['address_no_tone']
        
        # Combine title and address for matching
        place_text = f"{title} {address}".strip()
        place_text_no_tone = f"{title_no_tone} {address_no_tone}".strip()
        
        # Try matching against each entity
        max_score = 0.0
        
        for entity, entity_no_tone in zip(entities, entities_no_tone):
            # Match against original text
            token_set_score = fuzz.token_set_ratio(entity, place_text)
            partial_score = fuzz.partial_ratio(entity, place_text)
            score1 = (token_set_weight * token_set_score + partial_ratio_weight * partial_score) / (token_set_weight + partial_ratio_weight)
            
            # Match against text without tone marks
            token_set_score_no_tone = fuzz.token_set_ratio(entity_no_tone, place_text_no_tone)
            partial_score_no_tone = fuzz.partial_ratio(entity_no_tone, place_text_no_tone)
            score2 = (token_set_weight * token_set_score_no_tone + partial_ratio_weight * partial_score_no_tone) / (token_set_weight + partial_ratio_weight)
            
            # Also try matching full description
            desc_token_set = fuzz.token_set_ratio(description_no_tone, place_text_no_tone)
            desc_partial = fuzz.partial_ratio(description_no_tone, place_text_no_tone)
            score3 = (token_set_weight * desc_token_set + partial_ratio_weight * desc_partial) / (token_set_weight + partial_ratio_weight)
            
            max_score = max(max_score, score1, score2, score3)
        
        # Normalize to 0-1 range (fuzzy scores are 0-100)
        fuzzy_scores[place_id] = max_score / 100.0
    
    return fuzzy_scores

def computeNERScores(description: str, ner_data: Dict[str, np.ndarray], ner_model: SentenceTransformer, mode: str = 'max') -> Dict[int, float]:
    """
    Compute NER scores per place_id using the preprocessed database.
    Returns a dictionary with keys (place_id) and values (score).
    """
    if ner_data is None:
        return {}
    
    # Encode the query
    query_embedding = ner_model.encode([description], convert_to_numpy=True, normalize_embeddings=True)
    query_embedding = query_embedding[0]  # Get single embedding
    
    # Get embeddings and place_ids from ner_data
    embeddings = ner_data['embeddings']  # Shape: (num_sentences, embedding_dim)
    place_ids = ner_data['index']  # Shape: (num_sentences,)
    
    # Compute cosine similarity for all sentences
    cosine_similarities = np.dot(embeddings, query_embedding)  # Shape: (num_sentences,)
    
    # Group scores by place_id
    ner_scores = {}
    for place_id, score in zip(place_ids, cosine_similarities):
        if place_id not in ner_scores:
            ner_scores[place_id] = []
        ner_scores[place_id].append(score)
    
    # Aggregate scores per place_id based on mode
    if mode == 'max':
        ner_scores = {place_id: float(max(scores)) for place_id, scores in ner_scores.items()}
    elif mode == 'mean':
        ner_scores = {place_id: float(np.mean(scores)) for place_id, scores in ner_scores.items()}
    else:
        raise ValueError(f"Invalid mode for NER: {mode}")
    
    return ner_scores

@timing
def DescriptionToSuggestedPlaces(
    description: str, num_top_results: int = 5, mode='max', 
    clip_weight: float = 0.33, ner_weight: float = 0.33, fuzzy_weight: float = 0.34,
    **kwargs) -> List[int]:
    """
    Combine CLIP, NER, and fuzzy matching scores to return top place_ids.
    
    Args:
        description: Text description to search for
        num_top_results: Number of top results to return
        mode: Aggregation mode ('max', 'mean', or 'weighted')
        clip_weight: Weight for CLIP scores (default 0.33)
        ner_weight: Weight for NER scores (default 0.33)
        fuzzy_weight: Weight for fuzzy matching scores (default 0.34)
        **kwargs: Additional arguments for CLIP model (e.g., weight for weighted mode)
    
    Returns:
        List of top place_ids
    """
    # Compute CLIP scores
    text_embedding = embedText(model, description)
    clip_scores = computeCLIPScores(text_embedding, grouped_images, mode, **kwargs)
    
    # Compute NER scores (sentence transformer semantic search)
    ner_scores = computeNERScores(description, ner_data, ner_model, mode='max')
    
    # Extract entities using spaCy NER and compute fuzzy scores
    entities = extract_entities(description, spacy_ner_model)
    fuzzy_scores = computeFuzzyScores(description, entities, places_names_data)
    
    print(f"Extracted entities: {entities}")
    
    # Get all unique place_ids
    all_place_ids = set(clip_scores.keys())
    if ner_scores:
        all_place_ids.update(ner_scores.keys())
    if fuzzy_scores:
        all_place_ids.update(fuzzy_scores.keys())
    
    # Combine scores
    combined_scores = {}
    for place_id in all_place_ids:
        clip_score = clip_scores.get(place_id, 0.0)
        ner_score = ner_scores.get(place_id, 0.0)
        fuzzy_score = fuzzy_scores.get(place_id, 0.0)
        
        # Normalize weights
        total_weight = clip_weight + ner_weight + fuzzy_weight
        combined_score = (clip_weight * clip_score + ner_weight * ner_score + fuzzy_weight * fuzzy_score) / total_weight
        combined_scores[place_id] = combined_score
    
    # Sort by combined score and return top place_ids
    sorted_places = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    top_place_ids = [place_id for place_id, score in sorted_places[:num_top_results]]
    
    print(f"Top {num_top_results} place_ids: {top_place_ids}")
    print(f"Top scores: {[combined_scores[pid] for pid in top_place_ids]}")
    
    return top_place_ids

def test():
    description = "Banh mi Oanh to enjoy cultural banh mi in HCM"
    suggested_places = DescriptionToSuggestedPlaces(description, num_top_results=3, mode='weighted')
    return suggested_places

if __name__ == "__main__":
    preload()
    test()