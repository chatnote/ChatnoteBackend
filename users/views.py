import urllib.parse
from datetime import datetime

from django.shortcuts import render

from cores.apis import api, api_v2
from cores.auths import CustomJwtTokenAuth, GlobalAuth
from cores.enums import ApiTagEnum
from users.enums import SignupEnum
from users.models import User
from users.schemas import UserSchema, SignUpParams, LoginParams, LoginResponse, SignUpResponse, GoogleSignupParams, \
    AppleSignupParams
from users.services import GoogleLoginService, AppleLoginService


@api.get(
    path="user/",
    response={200: UserSchema},
    tags=[ApiTagEnum.user]
)
@api_v2.get(
    path="user/",
    response={200: UserSchema},
    tags=[ApiTagEnum.user]
)
def get_user(request):
    user = request.user
    return UserSchema.from_instance(user)


@api.post(
    path="user/delete/",
    tags=[ApiTagEnum.user]
)
def delete_user(request):
    user = request.user
    user.is_active = False
    user.email = user.email + str(datetime.now())
    user.google_access_token = None
    user.apple_access_token = None
    user.notion_access_token = None
    user.save()


@api.get(
    path="login/google/callback/",
    auth=None,
    response={200: SignUpResponse},
    tags=[ApiTagEnum.user]
)
@api_v2.get(
    path="login/google/callback/",
    auth=None,
    response={200: SignUpResponse},
    tags=[ApiTagEnum.user]
)
def google_callback(request, code: str, redirect_url: str):
    code = urllib.parse.unquote(code)
    access_token = GoogleLoginService.get_token(code, redirect_url)
    tokens = GoogleLoginService.get_account_info(access_token)
    email = tokens["email"]
    picture = tokens["picture"]

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create(email=email)

    user.google_profile_image = picture
    user.google_access_token = access_token
    user.save()

    token = CustomJwtTokenAuth().encode_jwt(user, SignupEnum.google)
    return SignUpResponse(token=token, user=user)


@api.get(
    path="login/apple/callback/",
    auth=None,
    response={200: SignUpResponse},
    tags=[ApiTagEnum.user],
    deprecated=True
)
def signup_apple(request, code: str, redirect_url: str):
    access_token = AppleLoginService.get_token(code, redirect_url)
    email = AppleLoginService.get_email(access_token)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create(email=email)

    token = CustomJwtTokenAuth().encode_jwt(user, SignupEnum.apple)
    return SignUpResponse(token=token, user=user)
