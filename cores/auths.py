import time

from django.conf import settings
from ninja.security import HttpBearer

from cores.enums import InvalidJwtErrorEnum
from cores.exception import CustomException
from datetime import datetime
import jwt


class CustomJwtTokenAuth:
    JWT_ALGORITHM = "HS256"
    EXP_TIME = 60 * 60 * 24 * 365

    def __init__(self):
        pass

    def encode_jwt(self, user, login_type):
        payload = {
            "id": user.id,
            "email": user.email,
            "iss": login_type,  # open id 에 존재하는 필드 사용
            "exp_time": int(time.mktime(datetime.now().timetuple())) + self.EXP_TIME
        }
        token = jwt.encode(
            payload, settings.SECRET_KEY, algorithm=self.JWT_ALGORITHM
        )
        return token

    def decode_jwt_to_user(self, token: str):
        from users.models import User

        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[self.JWT_ALGORITHM]
            )
        except (jwt.ExpiredSignatureError, jwt.DecodeError, jwt.InvalidTokenError) as e:
            raise CustomException(error_code=InvalidJwtErrorEnum.invalid_jwt, status_code=401)

        user_id = payload.get("id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise CustomException(error_code=InvalidJwtErrorEnum.invalid_jwt, status_code=401)
        return user


class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        from users.models import User
        if token in settings.ACCESS_ALLOWED_EMAILS:
            user = User.objects.get(email=token)
            request.user = user
            return token

        user = CustomJwtTokenAuth().decode_jwt_to_user(token)

        is_valid = User.validate(user)
        if is_valid:
            request.user = user
        else:
            raise CustomException(error_code=InvalidJwtErrorEnum.invalid_jwt, status_code=401)

        return token
