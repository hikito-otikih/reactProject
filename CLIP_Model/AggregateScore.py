from typing import Callable, List, Dict, Any
import numpy as np
import faiss
import constant
from util import imageIdsToPlaceIdsAndUrls
from collections import OrderedDict
from sentence_transformers import util as TransformerUtil
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
        imagesData is a list of dictionaries with these following keys exist: score
        return the mean score
        """
        return np.mean([imageData["score"] for imageData in imagesData], axis=0).astype(np.float32)
    return mean

def weightedScore(**kwargs) -> Aggregator:
    try:
        weight_for_main_image = kwargs["weight"] if "weight" in kwargs else 1.3
    except KeyError:
        raise ValueError("weights are required for weighted score aggregator")
    def weighted(imagesData: List[Dict[str, Any]]) -> np.float32:
        """
        imagesData is a list of dictionaries with these following keys exist: isMainImage, score
        return the weighted score
        """
        weights = [weight_for_main_image if imageData["isMainImage"] else 1 for imageData in imagesData]
        weights /= np.sum(weights)

        return np.sum([imageData["score"] * weight for imageData, weight in zip(imagesData, weights)]).astype(np.float32)
    return weighted

def maxScore(**kwargs) -> Aggregator:
    def max(imagesData: List[Dict[str, Any]]) -> np.float32:
        """
        imagesData is a list of dictionaries with these following keys exist: score
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

def buildFaiss(grouped_images: Dict[int, List[Dict[str, Any]]], mode: str = 'mean', **kwargs) -> faiss.Index:
    aggregator = aggregateFunc(mode, **kwargs)

    new_faiss_index = faiss.IndexFlatIP(constant.DIMENSION)

    for place_id, imagesData in grouped_images.items():
        score = aggregator(imagesData)
        new_faiss_index.add_with_ids([score], np.array([place_id]))
    return new_faiss_index

def findBestMatch(text_embedding: np.ndarray, grouped_images: Dict[int, List[Dict[str, Any]]], index: faiss.Index, mode: str = 'max', num_top_results: int = 5, **kwargs) -> Dict[int, List[int]]:
    """
    text_embedding is a numpy array of the text embedding.
    grouped_images is a dictionary with keys (place_id) and values (list of dictionaries with these keys exist: rowid, url, isMainImage, embedding))
    index is a faiss index.
    mode is the mode of the score aggregation.
    num_top_results is the number of top results to return.

    return a dictionary with keys (place_id) and values (list of matching (id, url) 's in the place). 
    If mode is 'weighted', then values is list of all (id, url) in the place.
    """
    if mode == 'max':
        more_num_results = num_top_results * 2;
        similarityScore, ids = index.search(text_embedding.reshape(1, -1), more_num_results) ## top k places
        ids_list = ids[0]
        print("ids_list: ", ids_list)
        print("similarityScore: ", similarityScore)
        imgIdToPlaceIdsAndUrls = imageIdsToPlaceIdsAndUrls(ids_list)
        groupByPlaceID = {}

        for id in ids_list:
            placeIdAndUrl = imgIdToPlaceIdsAndUrls[id]
            if placeIdAndUrl["place_id"] not in groupByPlaceID:
                groupByPlaceID[placeIdAndUrl["place_id"]] = []
            groupByPlaceID[placeIdAndUrl["place_id"]].append((id, placeIdAndUrl["url"]))

        return groupByPlaceID

    if mode == 'weighted':
        mainImageWeight = kwargs["weight"] if "weight" in kwargs else 1.5
        print("mainImageWeight: ", mainImageWeight)
        ScoreDict = {}
        for place_id, value in grouped_images.items():
            embeddingList = [imageData["embedding"] for imageData in value]
            weights = [mainImageWeight if imageData["isMainImage"] else 1 for imageData in value]
            sum = (1 * (len(weights) - 1) + mainImageWeight)
            weights = [weight / sum for weight in weights]
            # print("weights: ", weights)
            overallEmbedding = np.sum([embedding * weight for embedding, weight in zip(embeddingList, weights)], axis=0).astype(np.float32)
            assert overallEmbedding.shape == (constant.DIMENSION,), "overallEmbedding must be a numpy array of shape (DIMENSION,)"
            ScoreDict[place_id] = TransformerUtil.cos_sim(overallEmbedding, text_embedding)

        OrderedScoreDict = list(ScoreDict.items())
        OrderedScoreDict.sort(key=lambda x: x[1], reverse=True)

        print("OrderedScoreDict: ", OrderedScoreDict[:10])

        first_k_place_ids = [x[0] for x in OrderedScoreDict][:num_top_results]

        groupByPlaceID = {}
        for place_id in first_k_place_ids:
            groupByPlaceID[place_id] = [(imageData["rowid"], imageData['url']) for imageData in grouped_images[place_id]]
        return groupByPlaceID
    else:
        raise ValueError(f"Invalid mode: {mode}")