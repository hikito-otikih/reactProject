## create a parent class for search model
from typing import Any, List
import numpy as np


# class EmbeddingStorage:
#     def __init__(self, model: Any, storage_path: str):
#         self.model = model 
#         self.storage_path = storage_path
#     def preprocessDatabase(self, data):
#         raise NotImplementedError("Subclasses must implement this method")
#     def processQuery(self, query: Any) -> np.array:
#         raise NotImplementedError("Subclasses must implement this method")


class ModelEmbeddng:
    def __init__(self, model: Any, storage_path: str):
        self.model = model ## Load by yourself
        self.storage_path = storage_path
    def encodingQuery(self, query: Any) -> np.array: ## query can either text or image, either list or not list
        ## one may easily override this if needed
        return self.model.encode(query, convert_to_numpy=True)
    def preprocessDatabase(self, data):
        raise NotImplementedError("Subclasses must implement this method")
    def computeSimilarityScore(self, query: Any) -> np.array:
        raise NotImplementedError("Subclasses must implement this method")
