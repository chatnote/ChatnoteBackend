from datetime import datetime

from django.shortcuts import render

from cores.apis import api
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
def google_callback(request, ccode: str):
    access_token = GoogleLoginService.get_token(code)
    email = GoogleLoginService.get_email(access_token)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create(email=email)

    token = CustomJwtTokenAuth().encode_jwt(user, SignupEnum.google)
    return SignUpResponse(token=token, user=user)


@api.get(
    path="login/apple/callback/",
    auth=None,
    response={200: SignUpResponse},
    tags=[ApiTagEnum.user]
)
def signup_apple(request, code: str):
    access_token = AppleLoginService.get_token(code)
    email = AppleLoginService.get_email(access_token)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create(email=email)

    token = CustomJwtTokenAuth().encode_jwt(user, SignupEnum.apple)
    return SignUpResponse(token=token, user=user)
