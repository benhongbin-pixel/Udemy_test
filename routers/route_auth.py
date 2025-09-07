from fastapi import APIRouter
from fastapi import Response, Request, Depends
from fastapi.encoders import jsonable_encoder
from schemas import UserBody, SuccessMsg, UserInfo, Csrf
from database import (
    db_signup,
    db_login,
)
from auth_utils import AuthJwtCsrf
from fastapi_csrf_protect import CsrfProtect

router = APIRouter()
auth = AuthJwtCsrf()

#token取得
#テスト済み
@router.get("/api/csrftoken")
def get_csrf_token(response: Response, csrf_protect: CsrfProtect = Depends()):
    # 新API: tuple を返す
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    # サイン済みの方を Cookie に保存（Double Submit Cookie パターン）
    csrf_protect.set_csrf_cookie(signed_token, response)
    # 便利のためヘッダーにも載せておくとクライアントが拾いやすい
    response.headers["X-CSRFToken"] = csrf_token
    return {"csrf_token": csrf_token}

#test済み
@router.post("/api/register", response_model=UserInfo)
async def signup(request: Request, user: UserBody, csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)
    user = jsonable_encoder(user)
    new_user = await db_signup(user)
    return new_user

#テスト済み
@router.post("/api/login", response_model=SuccessMsg)
async def login(request: Request, response: Response, user: UserBody, csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)
    user = jsonable_encoder(user)
    token = await db_login(user)
    response.set_cookie(
        key="access_token", value=f"Bearer {token}", httponly=True, samesite="none", secure=True)
    return {"message": "Successfully logged-in"}

#テスト済み
@router.post("/api/logout", response_model=SuccessMsg)
async def logout(request: Request, response: Response, csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)

    response.set_cookie(key="access_token", value="",
                        httponly=True, samesite="none", secure=True)
    return {'message': 'Successfully logged-out'}

#テスト済み
#ログイン時のみ有効
@router.get('/api/user', response_model=UserInfo)
def get_user_refresh_jwt(request: Request, response: Response):
    new_token, subject = auth.verify_update_jwt(request)
    response.set_cookie(
        key="access_token", value=f"Bearer {new_token}", httponly=True, samesite="none", secure=True)
    return {'email': subject}