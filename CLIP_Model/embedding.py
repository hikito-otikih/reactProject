from sentence_transformers import SentenceTransformer
from constant import original_DB_path, images_embedding_DB_path, places_table_name, images_table_name
import sqlite3
import json
from PIL import Image
import requests
import numpy as np
import faiss
from tqdm import tqdm

from init_model import load_CLIP_model


def imagesEmbeddingForDatabase():
    """
    imagesEmbeddingForDatabase is a function that embeds the images for the database.
    """
    model = load_CLIP_model()
    

    def getImagesJson():
        conn = sqlite3.connect(original_DB_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT rowid, images FROM {places_table_name}")
        images = cursor.fetchall()
        cursor.close()
        conn.close()
        return [(imagejson[0], imagejson[1]) for imagejson in images]
    def ProcessJsonString(jsonStringAndID):
        """
        jsonStringAndID is a tuple of (id, json string), which can be converted to a list of image paths.

        return a list of dictionaries with the following keys: id, url, img, embedding.
        type of id: int, type of url: str, type of img: PIL.Image.Image, type of embedding: numpy.ndarray.
        """
        id, urlList = jsonStringAndID
        urlList = json.loads(urlList)
        assert isinstance(urlList, list), "urlList must be a list of urls"
        assert isinstance(id, int), "id must be an integer"

        imgList = []
        for url in urlList:
            try:
                img = Image.open(requests.get(url, stream=True).raw)
                imgList.append(img)
            except Exception as e:
                print(f"Error opening image {url}: {e}")
                continue
        embeddingList = [model.encode(img) for img in imgList]
        return [{"id": id, "url": url, "img": img, "embedding": embedding} for url,img,embedding in zip(urlList,imgList,embeddingList)]

    # def expandToSameLen(ListOfEmbeddingList):
    #     """
    #     ListOfEmbeddingList is a list of list of embeddings.

    #     return that list with each element having the same length of the longest list.
    #     """
    #     maxLen = max([len(embeddingList) for embeddingList in ListOfEmbeddingList])
    #     shape = ListOfEmbeddingList[0][0].shape
    #     return [embeddingList + [np.zeros(shape)] * (maxLen - len(embeddingList)) for embeddingList in ListOfEmbeddingList]

    AllImageList = getImagesJson()
    
    ListOfImageInfoList = []
    for imageJsonAndID in tqdm(AllImageList):
        imageInfoList = ProcessJsonString(imageJsonAndID)
        ListOfImageInfoList.append(imageInfoList)

    return ListOfImageInfoList


def UtilPrintImageInfoList(ListOfImageInfoList):
    """
    shorter_print is a function that prints the embeddings in a shorter way.

    **for testing purpose**
    """
    for imginfoList in ListOfImageInfoList:
        for imginfo in imginfoList:
            print(imginfo["id"])
            print(imginfo["url"])
            print(imginfo["img"])
            print(imginfo["embedding"][:10])
            print("-"*100)

def buildImagesTable(ListOfImageInfoList, table_name = images_table_name):
    """
    build images table named {table_name} and add to database {DB_path}
    """
    conn = sqlite3.connect(images_embedding_DB_path)
    cursor = conn.cursor()
    ## multiple images can share the same place_id
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (place_id INTEGER, url TEXT, embedding BLOB, isMainImage BOOLEAN NOT NULL DEFAULT FALSE)")
    for imginfoList in ListOfImageInfoList:
        for i, imginfo in enumerate(imginfoList):
            isMainImage = (i == 0)
            cursor.execute(f"INSERT INTO {table_name} (place_id, url, embedding, isMainImage) VALUES (?, ?, ?, ?)", (imginfo["id"], imginfo["url"], imginfo["embedding"], isMainImage))
    conn.commit()
    cursor.close()
    conn.close()

def databaseToFaiss(table_name = images_table_name):
    """
    databaseToFaiss is a function that converts the database to a faiss index.
    """
    conn = sqlite3.connect(images_embedding_DB_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT embedding FROM {table_name}")
    embeddings = cursor.fetchall() ## list of blobs
    ## convert to numpy array 2d
    embeddings = np.array([np.frombuffer(embedding[0], dtype=np.float32) for embedding in embeddings])
    assert embeddings.ndim == 2, "embeddings must be a 2D array"

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, f"{table_name}.bin")

    cursor.close()
    conn.close()
    print(f"Faiss index written to {table_name}.bin success")
    return index


if __name__ == "__main__":
    AllImageEmbeddingList = imagesEmbeddingForDatabase()
    UtilPrintImageInfoList(AllImageEmbeddingList)

    buildImagesTable(AllImageEmbeddingList, table_name = "test_images")
    print("Images table built successfully")

    index = databaseToFaiss(table_name = "test_images")
    print("Faiss index built successfully")

    