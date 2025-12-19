from typing import List, Dict
import constant
import numpy as np
import os
from sentence_transformers import SentenceTransformer
import spacy
from searchModel import FaissScoreMachine, MatrixScoreMachine, FuzzyMatchingScoreMachine
from util import timing, printPlaceList, load_CLIP_model

## 
def preload():
    global clip_machine, ner_machine, fuzzy_machine
    
    # Initialize CLIP machine (FaissScoreMachine)
    clip_model = load_CLIP_model()
    clip_machine = FaissScoreMachine(
        model=clip_model,
        index_file_path=constant.index_file_path,
        db_path=constant.images_embedding_DB_path,
        table_name=constant.images_table_name
    )
    print("CLIP machine initialized")
    
    # Initialize NER machine (MatrixScoreMachine)
    ner_model = SentenceTransformer("paraphrase-mpnet-base-v2")
    ner_data_path = os.path.join("model_testing", "arrays.pkl")
    if os.path.exists(ner_data_path):
        # Store the NER model for encoding queries
        ner_machine = MatrixScoreMachine(
            model=ner_model,
            storage_path=ner_data_path
        )
        print("NER machine initialized")
    else:
        ner_machine = None
        print(f"Warning: NER data file not found at {ner_data_path}")
    
    # Initialize Fuzzy matching machine (FuzzyMatchingScoreMachine)
    try:
        spacy_ner_model = spacy.load("xx_ent_wiki_sm")
        print("spaCy NER model (xx_ent_wiki_sm) loaded successfully")
    except Exception as e:
        spacy_ner_model = None
        print(f"Warning: spaCy NER model could not be loaded: {e}")
        print("You may need to install it with: python -m spacy download xx_ent_wiki_sm")
    
    fuzzy_machine = FuzzyMatchingScoreMachine(
        model=None,  # Not used for fuzzy matching
        storage_path="places_names.db",
        table_name="places_names",
        nlp_model=spacy_ner_model
    )
    print("Fuzzy matching machine initialized")

@timing
def DescriptionToSuggestedPlaces(
    description: str, num_top_results: int = 5,
    clip_weight: float = 0.3, ner_weight: float = 0.5, fuzzy_weight: float = 0.2,
    **kwargs) -> List[int]:
    """
    Combine CLIP, NER, and fuzzy matching scores to return top place_ids.
    
    Args:
        description: Text description to search for
        num_top_results: Number of top results to return
        mode: Aggregation mode ('max', 'mean', or 'weighted') for CLIP
        clip_weight: Weight for CLIP scores (default 0.3)
        ner_weight: Weight for NER scores (default 0.5)
        fuzzy_weight: Weight for fuzzy matching scores (default 0.2)
        **kwargs: Additional arguments for CLIP model (e.g., weight for weighted mode)
    
    Returns:
        List of top place_ids
    """
    # Compute CLIP scores using CLIP machine, clip_id using original DB rowid
    clip_place_ids, clip_scores = clip_machine.computeSimilarityScore(description, mode='weighted', **kwargs)
    
    # Compute NER scores using NER machine
    _, ner_scores = ner_machine.computeSimilarityScore(description)
    # Compute fuzzy matching scores using fuzzy machine
    _, fuzzy_scores = fuzzy_machine.computeSimilarityScore(description)

    combined_scores = clip_scores * clip_weight + ner_scores * ner_weight + fuzzy_scores * fuzzy_weight
    sorted_scores = np.argsort(combined_scores)[::-1]

    top_place_ids = clip_place_ids[sorted_scores[:num_top_results]]
    print ("top clip score: ", clip_scores[sorted_scores[:num_top_results]])
    print ("top ner score: ", ner_scores[sorted_scores[:num_top_results]])
    print ("top fuzzy score: ", fuzzy_scores[sorted_scores[:num_top_results]])
    print("top_place_ids: ", top_place_ids)
    printPlaceList(top_place_ids)
    return top_place_ids


def test():
    description = "japanese food shop in ho chi minh city"
    suggested_places = DescriptionToSuggestedPlaces(description, num_top_results=3)

if __name__ == "__main__":
    preload()
    test()