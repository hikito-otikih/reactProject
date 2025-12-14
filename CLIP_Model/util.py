import sqlite3
from typing import List, Dict, Any
import constant
import json
import numpy as np
from sentence_transformers import util as TransformerUtil
import time

def batchIterator(iterable, batch_size: int = 16):
    """
    return an iterator that yields batches of the iterable
    """
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i+batch_size]

def findPlacesFromIds(ids: List[np.ndarray]) -> Dict[int, List[Dict[str, Any]]]:
    """
    find places from ids
    return a dictionary with keys (place_id) and values (list of dictionaries with keys (rowid, url))
    """

    ids = ids[0]
    ids_as_string = ','.join(str(id) for id in ids)
    print("ids_as_string: ", ids_as_string)
    conn = sqlite3.connect(constant.images_embedding_DB_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT rowid, place_id, url FROM {constant.images_table_name} WHERE rowid IN ({ids_as_string})")
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    places_dict = {}
    for rowid, place_id, url in result:
        if place_id not in places_dict:
            places_dict[place_id] = []
        places_dict[place_id].append({"rowid": rowid, "url": url})
    print("Found: ", len(places_dict), " places")

    for place_id, value in places_dict.items():
        print("Place ID: ", place_id)
        for item in value:
            print("Row ID: ", item["rowid"], " URL: ", item["url"])
        print("-"*100)
    return places_dict ## dictionary with keys (place_id) and values (list of dictionaries with keys (rowid, url))
    
def computeScore(text_embedding: np.ndarray, grouped_images: Dict[int, List[Dict[str, Any]]]) -> Dict[int, List[Dict[str, Any]]]:
    """
    "grouped_images" is a dictionary with keys (place_id) and values (list of dictionaries with these following keys exist: embedding)
    "text_embedding" is a numpy array of the text embedding.
    return that list of dict with key 'score' added.
    """
    for place_id, imagesData in grouped_images.items():
        for imageData in imagesData:
            imageData.append({"score": TransformerUtil.cos_sim(text_embedding, imageData["embedding"])})
    return grouped_images

def imageIdsToPlaceIdsAndUrls(ids: List[np.ndarray]) -> Dict[int, List[Dict[str, Any]]]:
    """
    in order for not losing order, return a dictionary rowid -> place_id
    """
    ids_as_string = ','.join(str(id) for id in ids)
    conn = sqlite3.connect(constant.images_embedding_DB_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT rowid, place_id, url FROM {constant.images_table_name} WHERE rowid IN ({ids_as_string})")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    rowidToPlaceIdAndUrl = {rowid: {"place_id": place_id, "url": url} for rowid, place_id, url in result}
    return rowidToPlaceIdAndUrl   

def printBestMatchUtility(best_match: Dict[int, List[Dict[str, Any]]]):
    """
    key is place id
    value is list of tuples (rowid, url)
    """
    for place_id, imagesData in best_match.items():
        print("Place ID: ", place_id)
        for imageData in imagesData:
            print("Row ID: ", imageData[0], " URL: ", imageData[1])
        print("-"*100)
    
## declare decorator for timing
## add annotation for the function
def timing(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time taken: {end_time - start_time} seconds")
        return result
    return wrapper