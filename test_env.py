from decouple import config

print("MONGO_API_KEY =", config("MONGO_API_KEY", default=None))
