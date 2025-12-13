from typing import List, Dict, Any
import constant
import sqlite3
import json
import numpy as np

from init_model import embedText
from loadFaiss import loadEmbeddingData
# from AggregateScore import computeScore
from util import findPlacesFromIds

def DescriptionToSuggestedPlaces(
    description: str, num_top_images: int = 5, mode='max') -> List[Dict[str, Any]]:
    """
    return a dictionary with keys (place_id) and values (list of dictionaries with keys (rowid, url))
    """
    text_embedding = embedText(description)

    index, grouped_images = loadEmbeddingData()
    similarityScore, ids = index.search(text_embedding.reshape(1, -1), num_top_images)
    ids = [id + 1 for id in ids] ## faiss index is 0-based, but rowid is 1-based
    print("similarityScore: ", similarityScore)
    print("ids: ", ids)

    places_dict = findPlacesFromIds(ids)
    return places_dict

def getImageListFromResult(result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    read from places database to get the image list
    """
    conn = sqlite3.connect(constant.original_DB_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT images FROM {constant.places_table_name} WHERE place_id = ?", (result['place_id'],))
    images = cursor.fetchone()
    ## convert each element from tuple (a,) to a
    images = ([image[0] for image in images])
    imagesjson = [json.loads(image) for image in images]
    cursor.close()
    conn.close()
    return imagesjson

if __name__ == "__main__":
    description = "Đồ ăn Nhật bản ngon"
    suggested_places = DescriptionToSuggestedPlaces(description, num_top_images=3)
