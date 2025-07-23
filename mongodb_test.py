from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  # ← 이 줄을 추가해야 .env 읽음

# cluster=MongoClient("mongodb+srv://mokash1ae:ysisebas420%21@cluster0.3zciq5d.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

cluster = MongoClient(os.getenv("MONGO_CLUSTER_URI"))
db = cluster["duri"]
collection = db["chats"]

my_friend = {
    "name": "두리쥐",
    "age": 26,
    "job": "포켓몬스터",
    "character": "당신은 진지한 것을 싫어하며, 항상 밝고 명랑한 성격임",
    "best friend": {"name": "사용자",
                    "situations": ["짝꿍쥐와 항상 함께 다님",
                                   "음식을 사이좋게 나누어 먹고 싶어함",
                                   "'파밀리쥐'로 진화하고 싶어함"]
                    }
}

collection.insert_one(my_friend)

for result in collection.find({}):
    print(result)
