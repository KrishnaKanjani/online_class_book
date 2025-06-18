
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

def custom_jsonable_encoder(obj):
   if isinstance(obj, ObjectId):
      return str(obj)
   if isinstance(obj, list):
      return [custom_jsonable_encoder(item) for item in obj]
   if isinstance(obj, tuple):
      return (custom_jsonable_encoder(item) for item in obj)
   if isinstance(obj, dict):
      return {key: custom_jsonable_encoder(value) for key, value in obj.items()}
   if isinstance(obj, set):
      return {custom_jsonable_encoder(value) for value in obj}
   return jsonable_encoder(obj)