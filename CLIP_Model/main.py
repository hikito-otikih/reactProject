from typing import List, Dict, Any
import constant
import sqlite3
import json
import numpy as np
import faiss
import time

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
    global model, index, grouped_images

    model = load_CLIP_model()
    index, grouped_images = loadEmbeddingData()

@timing
def DescriptionToSuggestedPlaces(
    description: str, num_top_results: int = 5, mode='max', **kwargs) -> List[int]:
    """
    return a dictionary with keys (place_id) and values (list of dictionaries with keys (rowid, url))
    """
    text_embedding = embedText(model, description)

    best_match = findBestMatch(text_embedding, grouped_images, index, mode, num_top_results, **kwargs)

    printBestMatchUtility(best_match)
    return best_match
    # best_match is a dictionary with keys (place_id) and values (list of all matching images). 

    # grouped_images_and_scores = computeScore(text_embedding, grouped_images) 
    # ## dictionary with keys (place_id) and values (list of dictionaries with these following keys exist: score)

    # new_faiss_index = buildFaiss(grouped_images_and_scores, mode, **kwargs)
    # faiss.write_index(new_faiss_index, "new_faiss_index.bin")

    # similarityScore, ids = new_faiss_index.search(text_embedding.reshape(1, -1), num_top_results) ## top k places
    # print("similarityScore: ", similarityScore)
    # print("ids: ", ids)
    # ids_list = ids[0]
    # print(fetchImageListFromIds(ids_list)) ## ids is 2 dim array
    # return ids_list

def test():
    description = "Japanese food"
    suggested_places = DescriptionToSuggestedPlaces(description, num_top_results=3, mode='weighted')
    return suggested_places

if __name__ == "__main__":
    preload()
    test()