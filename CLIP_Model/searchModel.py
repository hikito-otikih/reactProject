## create a parent class for search model
from ast import Pass
from typing import Any, List, Optional, Dict
import numpy as np
import os
import pickle
import faiss
import sqlite3
from sentence_transformers import util as TransformerUtil
from rapidfuzz import fuzz
import unicodedata
import spacy

class ScoreMachine:
    def __init__(self, **kwargs):
        pass

    def preprocessDatabase(self, data):
        pass
    def loadStorage(self):
        pass
    def computeSimilarityScore(self, query: str, **kwargs) -> np.array:
        pass

## each storage correspond to a different way to store the embedding
class FaissScoreMachine(ScoreMachine):
    def __init__(self, model: Any, index_file_path: str, db_path: str, table_name: str, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.index_file_path = index_file_path
        self.db_path = db_path
        self.table_name = table_name
        self.storage = self.loadStorage()

    def preprocessDatabase(self, data):
        pass
    def loadStorage(self):
        """
        return:
        - index: a faiss index
        - grouped_images: a dictionary with keys (place_id) and values (list of dictionaries with keys (rowid, url, isMainImage, embedding))
        """
        def loadFromFaiss():
            index = faiss.read_index(self.index_file_path)
            return index
    
        def loadFromImagesDatabase():
            """
            return a list of dictionaries with keys (rowid, place_id, url, isMainImage)
            """
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT place_id, url, isMainImage FROM {self.table_name}")
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            list_id = range(1, len(result) + 1)
            return [{"rowid": id, "place_id": imageData[0], "url": imageData[1], "isMainImage": imageData[2]} for id, imageData in zip(list_id, result)]
            
        def groupImagesByPlaceId(imagesData, index):
            """
            return: a dictionary with keys (place_id) and values (list of dictionaries with keys (rowid, url, isMainImage, embedding))
            """
            result = {}
            for imageData in imagesData:
                if imageData["place_id"] not in result:
                    result[imageData["place_id"]] = []
                item = {"rowid": imageData["rowid"], "url": imageData["url"], "isMainImage": imageData["isMainImage"], "embedding": index.reconstruct(imageData["rowid"])}
                result[imageData["place_id"]].append(item)
            return result
        
        index = loadFromFaiss()
        assert index is not None, "Faiss index not loaded"
        imagesData = loadFromImagesDatabase()
        assert imagesData is not None, "Images data not loaded"
        # assert len(imagesData) == index.ntotal, "Number of images data does not match number of embeddings"
        grouped_images = groupImagesByPlaceId(imagesData, index)
        assert grouped_images is not None, "Grouped images not loaded"
        return index, grouped_images

    def computeSimilarityScore(self, query: str, mode: str = 'max', **kwargs) -> np.array:
        """
        Compute similarity scores between query embedding and all places.
        Returns a numpy array of scores, one per place_id (sorted by place_id).
        """
        queryEmbedding = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
        assert queryEmbedding is not None, "Query embedding not computed"

        index, grouped_images = self.loadStorage()
        scores_dict = {}
        
        if mode == 'max':
            # For max mode, find the maximum similarity score among all images for each place
            for place_id, imagesData in grouped_images.items():
                max_score = -np.inf
                for imageData in imagesData:
                    embedding = imageData["embedding"]
                    # Reshape to 2D for cos_sim: (1, dim) and (1, dim)
                    score = TransformerUtil.cos_sim(
                        queryEmbedding.reshape(1, -1), 
                        embedding.reshape(1, -1)
                    ).item()
                    max_score = max(max_score, score)
                scores_dict[place_id] = max_score
        
        elif mode == 'weighted':
            # For weighted mode, compute weighted average of embeddings then similarity
            weight = kwargs.get("weight", 1.5)
            for place_id, imagesData in grouped_images.items():
                embeddingList = [imageData["embedding"] for imageData in imagesData]
                weights = [weight if imageData["isMainImage"] else 1 for imageData in imagesData]
                sum_weights = sum(weights)
                weights = [w / sum_weights for w in weights]
                overallEmbedding = np.sum([emb * w for emb, w in zip(embeddingList, weights)], axis=0).astype(np.float32)
                # Reshape to 2D for cos_sim
                score = TransformerUtil.cos_sim(
                    overallEmbedding.reshape(1, -1), 
                    queryEmbedding.reshape(1, -1)
                ).item()
                scores_dict[place_id] = score
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'max' or 'weighted'")
        ## no need to sort the score
        ## return index, score
        ## expect index = [1,2,...]
        index = np.array(list(scores_dict.keys()))
        scores = np.array(list(scores_dict.values()))

        index_sort = np.argsort(index)
        index = index[index_sort]
        scores = scores[index_sort]
        return index, scores

class MatrixScoreMachine(ScoreMachine):
    """
    Store the embedding in matrix
    """
    def __init__(self, model: Any, storage_path: str, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.storage_path = storage_path
        self.storage = self.loadStorage()
    def loadStorage(self):
        if not os.path.exists(self.storage_path):
            raise FileNotFoundError(f"Storage file not found at {self.storage_path}")
        try:
            with open(self.storage_path, 'rb') as f:
                data = pickle.load(f)
                index = data['index']
                embeddings = data['embeddings']
                return index, embeddings
        except Exception as e:
            raise Exception(f"Error loading storage: {e}")

    def preprocessDatabase(self, data):
        pass
    def computeSimilarityScore(self, query: str) -> np.array:
        queryEmbedding = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
        assert queryEmbedding is not None, "Query embedding not computed"
        
        index, embeddings = self.loadStorage()
        ScoreMatrix = np.dot(embeddings, queryEmbedding.T)
        ## take max score on rows with same index, like if index = [1,1,2,3], matrix = [0.25, 0.27, 0.4, 0.4]
        ## return [0.27, 0.4, 0.4] and [1,2,3]
        index = np.asarray(index)
        scores = np.asarray(ScoreMatrix)
        unique_index = np.unique(index)
        similarityScores = np.zeros(len(unique_index))
        for i, idx in enumerate(unique_index):
            similarityScores[i] = np.max(ScoreMatrix[index == idx])

        sort_id = np.argsort(unique_index)
        unique_index = unique_index[sort_id]
        similarityScores = similarityScores[sort_id]

        return unique_index, similarityScores

class FuzzyMatchingScoreMachine(ScoreMachine):
    def __init__(self, model: Any, storage_path: str, table_name: str = "places_names", nlp_model=None, **kwargs):
        super().__init__(**kwargs)
        self.storage_path = storage_path
        self.table_name = table_name
        self.model = model  # Not used for fuzzy matching, but kept for interface consistency
        self.nlp_model = nlp_model  # spaCy model for entity extraction (optional)
        self._places_names_data = None
        self.storage = self.loadStorage()
    
    def remove_tone_marks(self, text: str) -> str:
        """
        Remove Vietnamese tone marks (diacritics) from text.
        """
        if not text:
            return ""
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        text = unicodedata.normalize('NFC', text)
        return text
    
    def extract_entities(self, description: str) -> List[str]:
        """
        Extract named entities (PERSON, ORG, LOC, etc.) from description using spaCy NER model.
        Returns a list of entity text strings.
        """
        if self.nlp_model is None:
            return []
        
        try:
            doc = self.nlp_model(description)
            # Extract all named entities
            entities = [ent.text.strip() for ent in doc.ents if ent.text.strip()]
            # Filter out very short entities and return unique ones
            entities = [e for e in entities if len(e) > 1]
            return list(set(entities))  # Return unique entities
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return []
    
    def loadStorage(self):
        """
        Load places names data from the database.
        Returns a dictionary: {place_id: {'title': ..., 'title_no_tone': ..., 'address': ..., 'address_no_tone': ...}}
        """
        if self._places_names_data is not None:
            return self._places_names_data
        
        if not os.path.exists(self.storage_path):
            print(f"Warning: Places names database not found at {self.storage_path}")
            return None
        
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT place_id, title, title_no_tone, address, address_no_tone FROM {self.table_name}")
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
        
        self._places_names_data = places_data
        return self._places_names_data
    
    def computeSimilarityScore(self, query: str, token_set_weight: float = 0.5, partial_ratio_weight: float = 0.5, **kwargs) -> tuple:
        """
        Compute fuzzy matching scores by comparing query with place titles and addresses.
        
        Args:
            query: Text query to search for
            token_set_weight: Weight for token_set_ratio (default 0.5)
            partial_ratio_weight: Weight for partial_ratio (default 0.5)
        
        Returns:
            tuple: (index array, scores array) where index is place_ids and scores are similarity scores (0-1)
        """
        places_names_data = self.loadStorage()
        
        # Extract entities using spaCy NER (optional)
        entities = self.extract_entities(query)
        
        if not places_names_data:
            return np.array([]), np.array([])
        
        # Remove tone marks from query and entities for better matching
        query_no_tone = self.remove_tone_marks(query)
        entities_no_tone = [self.remove_tone_marks(e) for e in entities]
        
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
            
            # If we have entities, match against them
            if entities:
                for entity, entity_no_tone in zip(entities, entities_no_tone):
                    # Match against original text
                    token_set_score = fuzz.token_set_ratio(entity, place_text)
                    partial_score = fuzz.partial_ratio(entity, place_text)
                    score1 = (token_set_weight * token_set_score + partial_ratio_weight * partial_score) / (token_set_weight + partial_ratio_weight)
                    
                    # Match against text without tone marks
                    token_set_score_no_tone = fuzz.token_set_ratio(entity_no_tone, place_text_no_tone)
                    partial_score_no_tone = fuzz.partial_ratio(entity_no_tone, place_text_no_tone)
                    score2 = (token_set_weight * token_set_score_no_tone + partial_ratio_weight * partial_score_no_tone) / (token_set_weight + partial_ratio_weight)
                    
                    max_score = max(max_score, score1, score2)
            
            # Also try matching full description
            desc_token_set = fuzz.token_set_ratio(query_no_tone, place_text_no_tone)
            desc_partial = fuzz.partial_ratio(query_no_tone, place_text_no_tone)
            score3 = (token_set_weight * desc_token_set + partial_ratio_weight * desc_partial) / (token_set_weight + partial_ratio_weight)
            
            max_score = max(max_score, score3)
            
            # Normalize to 0-1 range (fuzzy scores are 0-100)
            fuzzy_scores[place_id] = max_score / 100.0
        
        # Convert to numpy arrays and sort by place_id
        index = np.array(list(fuzzy_scores.keys()))
        scores = np.array(list(fuzzy_scores.values()))
        index_sort = np.argsort(index)
        index = index[index_sort]
        scores = scores[index_sort]
        return index, scores
