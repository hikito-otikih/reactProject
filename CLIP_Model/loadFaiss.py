import faiss
import sqlite3
import constant
import numpy as np

def loadEmbeddingData(index_file_path = constant.index_file_path, db_path = constant.images_embedding_DB_path, table_name = constant.images_table_name):
    """
    return:
    - index: a faiss index
    - grouped_images: a dictionary with keys (place_id) and values (list of dictionaries with keys (rowid, isMainImage, embedding))
    """
    def loadFromFaiss():
        index = faiss.read_index(index_file_path)
        return index

    def loadFromImagesDatabase():
        """
        return a list of dictionaries with keys (rowid, place_id, isMainImage)
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT rowid, place_id, isMainImage FROM {table_name}")
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return [{"rowid": imageData[0], "place_id": imageData[1], "isMainImage": imageData[2]} for imageData in result]
    def groupImagesByPlaceId(imagesData, index):
        """
        return: a dictionary with keys (place_id) and values (list of dictionaries with keys (rowid, isMainImage, embedding))
        """
        result = {}
        for imageData in imagesData:
            if imageData["place_id"] not in result:
                result[imageData["place_id"]] = []
            result[imageData["place_id"]].append({"rowid": imageData["rowid"], "isMainImage": imageData["isMainImage"], "embedding": index.reconstruct(imageData["rowid"] - 1)}) 
            ## faiss index is 0-based, but rowid is 1-based
        return result
    
    index = loadFromFaiss()
    assert index is not None, "Faiss index not loaded"
    imagesData = loadFromImagesDatabase()
    assert imagesData is not None, "Images data not loaded"
    # assert len(imagesData) == index.ntotal, "Number of images data does not match number of embeddings"
    grouped_images = groupImagesByPlaceId(imagesData, index)
    assert grouped_images is not None, "Grouped images not loaded"
    return index, grouped_images
