import sqlite3
from typing import List, Dict, Any
import constant
import json
import numpy as np

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
    