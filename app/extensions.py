from pymongo import MongoClient
client = MongoClient('mongodb+srv://admin:admin@kanhai-cluster.fio7e.mongodb.net/github?retryWrites=true&w=majority')
db = client.github # Default DB name
githook = db.githook #Default Collection name
