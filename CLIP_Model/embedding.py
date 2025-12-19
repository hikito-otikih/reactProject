## fetch dữ liệu về
## for qua
## sparse cái string đó ra
## xong lại for qua từng url
## model.encode(image)

## thực ra cũng không cần lưu vào database cái embedding kia luôn
## mỗi lần for qua 1 ảnh, làm 2 việc: thêm nó vào database và thêm nó vào faiss index

from sentence_transformers import SentenceTransformer
from constant import original_DB_path, images_embedding_DB_path, places_table_name, images_table_name
import sqlite3
import json
from PIL import Image
import requests
import numpy as np
import faiss
from tqdm import tqdm
from util import batchIterator
from init_model import load_CLIP_model
import constant

def getIDsAndImageList():
    conn = sqlite3.connect(original_DB_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT rowid, images FROM {places_table_name}")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return [(imagejson[0], json.loads(imagejson[1])) for imagejson in result]

def buildImagesTable(IDsAndImageList, table_name = images_table_name):
    conn = sqlite3.connect(images_embedding_DB_path)
    cursor = conn.cursor()
    ## multiple images can share the same place_id
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (place_id INTEGER, url TEXT, isMainImage BOOLEAN NOT NULL DEFAULT FALSE)")
    for ID, imageList in IDsAndImageList:
        for i, img in enumerate(imageList):
            isMainImage = (i == 0)
            cursor.execute(f"INSERT INTO {table_name} (place_id, url, isMainImage) VALUES (?, ?, ?)", (ID, img, isMainImage))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Images table built successfully")

def databaseToFaiss(table_name = images_table_name):
    conn = sqlite3.connect(images_embedding_DB_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT rowid, url FROM {table_name}")
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    model = load_CLIP_model()

    remaining_ids_and_urls = []   
    
    dimension = constant.DIMENSION
    base_index = faiss.IndexFlatIP(dimension)
    index = faiss.IndexIDMap2(base_index)

    batchsize = 16

    for batch in tqdm(batchIterator(result, batchsize)):
        ids, imgs = [], []
        for id, url in batch:
            try:
                img = Image.open(requests.get(url, stream=True).raw).convert("RGB")
                ids.append(id)
                imgs.append(img)
            except Exception as e:
                print(f"Error opening image {url}: {e}")
                remaining_ids_and_urls.append((id, url))
                continue
        if len(imgs) == 0:
            continue

        embeddings = model.encode(imgs, batch_size=batchsize, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
        index.add_with_ids(embeddings, np.array(ids, dtype=np.int64))

    if len(remaining_ids_and_urls) > 0:
        print(f"Remaining {len(remaining_ids_and_urls)} ids and urls not encoded")
        with open("remaining_ids_and_urls.json", "w") as f:
            json.dump(remaining_ids_and_urls, f)
        print(f"Remaining ids and urls written to remaining_ids_and_urls.json")
        # return None

    ## final step: write index to file
    faiss.write_index(index, f"{table_name}.bin")
    print(f"Faiss index written to {table_name}.bin success")
    return index


if __name__ == "__main__":
    IDsAndImageList = getIDsAndImageList()

    buildImagesTable(IDsAndImageList)

    databaseToFaiss()




