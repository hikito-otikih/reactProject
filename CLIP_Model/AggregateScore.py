from typing import Callable, List, Dict, Any
import numpy as np

Aggregator = Callable[[List[Dict[str, Any]]], np.float32] ## type of score is np.float32 from faiss


def aggregateFunc(mode = 'mean', **kwargs) -> Aggregator:
    """
    mode can be either 'mean' or 'weighted' or 'max'
    return a function that aggregates the scores
    """
    if mode == 'mean':
        return meanScore(**kwargs)
    elif mode == 'weighted':    
        return weightedScore(**kwargs)
    elif mode == 'max':
        return maxScore(**kwargs)
    else:
        raise ValueError(f"Invalid mode: {mode}")

def meanScore(**kwargs) -> Aggregator:
    def mean(imagesData: List[Dict[str, Any]]) -> np.float32:
        """
        imagesData is a list of dictionaries with keys (isMainImage, embedding, score)
        return the mean score
        """
        return np.mean([imageData["score"] for imageData in imagesData], axis=0).astype(np.float32)
    return mean

def weightedScore(**kwargs) -> Aggregator:
    try:
        weight_for_main_image = kwargs["weight"]
    except KeyError:
        raise ValueError("weights are required for weighted score aggregator")
    def weighted(imagesData: List[Dict[str, Any]]) -> np.float32:
        """
        imagesData is a list of dictionaries with keys (isMainImage, embedding, score)
        return the weighted score
        """
        weights = [weight_for_main_image if imageData["isMainImage"] else 1 for imageData in imagesData]
        weights /= np.sum(weights)

        return np.sum([imageData["score"] * weight for imageData, weight in zip(imagesData, weights)]).astype(np.float32)
    return weighted

def maxScore(**kwargs) -> Aggregator:
    def max(imagesData: List[Dict[str, Any]]) -> np.float32:
        """
        imagesData is a list of dictionaries with keys (isMainImage, embedding, score)
        return the max score
        """
        return np.max([imageData["score"] for imageData in imagesData], axis=0).astype(np.float32)
    return max

# def computeScore(text_embedding: np.ndarray, index: faiss.Index, grouped_images: Dict[int, List[Dict[str, Any]]], mode: str = 'mean', num_top_places: int = 5) -> List[np.float32]:
#     """
#     text_embedding is a numpy array of the text embedding.
#     grouped_images is a dictionary with keys (place_id) and values (list of dictionaries with keys (rowid, isMainImage, embedding))
#     mode is the mode of the score aggregation.
#     num_top_places is the number of top places to return.

#     return a list of dictionaries with keys (place_id, score)
#     """
#     aggregator = aggregateFunc(mode)
#     allScores = [{'place_id': place_id, 'score': aggregator(imagesData)} 
#                 for place_id, imagesData in grouped_images.items()] ## list of dictionaries with keys (place_id, score)
#     allScores.sort(key=lambda x: x['score'], reverse=True)
#     return allScores[:num_top_places]
