from decouple import config
from fastapi import HTTPException
from typing import Union
import motor.motor_asyncio
from bson import ObjectId
#Randerの無料プランを用いてDeploy
import asyncio
from auth_utils import AuthJwtCsrf

MONGO_API_KEY = config('MONGO_API_KEY')

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_API_KEY)
#deploy用
client.get_io_loop = asyncio.get_event_loop
database = client.API_db
collection_todo = database.todo
collection_user = database.user
auth=AuthJwtCsrf()


def todo_serializer(todo) -> dict:
    return {
        "id": str(todo["_id"]),
        "title": todo["title"],
        "description": todo["description"]
    }

def user_serializer(user) ->dict:
    return{
        "id":str(user["_id"]),
        "email":user["email"],
    }

async def db_create_todo(data: dict) -> Union[dict, bool]:
    todo = await collection_todo.insert_one(data)
    new_todo = await collection_todo.find_one({"_id": todo.inserted_id})
    if new_todo:
        return todo_serializer(new_todo)
    return False


#get task todos
async def  db_get_todos() -> list:
    todos=[]
    #todoをデータベースから仕入れてそのままtodosに入れていく
    for todo in await collection_todo.find().to_list(length=100):
        todos.append(todo_serializer(todo))
    return todos

#一つのみを
async def db_get_single_todo(id:str) ->Union[dict,bool]:
    todo=await collection_todo.find_one({"_id":ObjectId(id)})
    if todo:
        return todo_serializer(todo)
    return False

#update
async def db_update_todo(id:str,data:dict) ->Union[dict,bool]:
    todo=await collection_todo.find_one({"_id":ObjectId(id)})#更新objectの確認
    if todo:
        update_todo=await collection_todo.update_one(
            {"_id":ObjectId(id)},{"$set":data}
        )
        #更新が成功しているときにMongoDBから更新データを読み込む
        if(update_todo.modified_count>0):
            new_todo=await collection_todo.find_one({"_id":ObjectId(id)})
            return todo_serializer(new_todo)
    return False

#delete
async def db_delete_todo(id:str) -> bool:
    todo=await collection_todo.find_one({"_id":ObjectId(id)})#更新objectの確認
    if todo:
        delete_todo=await collection_todo.delete_one( {"_id":ObjectId(id)})
        if(delete_todo.deleted_count>0):
            return True
    return False

#signup
async def db_signup(data:dict) -> dict:
    email=data.get("email")
    password=data.get("password")
    overlap_user=await collection_user.find_one({"email":email})
    #データの重複確認
    if overlap_user:
        raise HTTPException(status_code=400,detail="email is already taken")
    #check password
    if not password or len(password)<6:
        raise HTTPException(status_code=400,detail="password is too short")
    #ユーザー登録
    user=await collection_user.insert_one({"email":email,"password":auth.generate_hashed_pw(password)})
    #新しいユーザー情報の取得
    new_user = await collection_user.find_one({"_id": user.inserted_id})
    return user_serializer(new_user)

#login
async def db_login(data:dict) ->str:
    email=data.get("email")
    password=data.get("password")
    user = await collection_user.find_one({"email":email})
    #メールが有効でないとき
    if not user or not auth.verify_pw(password,user["password"]):
        raise HTTPException(
            status_code=401,detail="invalid email or password"
        )
    token=auth.encode_jwt(user["email"])
    return token


