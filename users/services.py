import requests
from django.conf import settings


class GoogleLoginService:
    def __init__(self):
        pass

    @staticmethod
    def get_token(code: str) -> str:
        # https://developers.google.com/identity/protocols/oauth2/web-server?hl=ko#exchange-authorization-code
        response = requests.post(
            url=f"https://oauth2.googleapis.com/token",
            headers={
                'Content-type': 'application/x-www-form-urlencoded',
                'charset': 'utf-8'
            },
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GOOGLE_CALLBACK_URI,
                "grant_type": "authorization_code",
            }
        )
        access_token = response.json()["access_token"]
        return access_token

    @staticmethod
    def get_email(access_token: str) -> str:
        response = requests.get(
            url="https://www.googleapis.com/oauth2/v2/userinfo",
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-type': 'application/x-www-form-urlencoded',
                'charset': 'utf-8'
            }
        )
        email = response.json()['email']
        return email


class AppleLoginService:
    def __init__(self):
        pass

    @staticmethod
    def get_token(code):
        response = requests.post(
            url="https://appleid.apple.com/auth/token",
            headers={
                'Content-type': 'application/x-www-form-urlencoded',
                'charset': 'utf-8'
            },
            data={
                'grant_type': 'authorization_code',
                'code': code,
                "client_id": settings.APPLE_CLIENT_ID,
                "client_secret": settings.APPLE_CLIENT_SECRET,
                'redirect_uri': settings.APPLE_REDIRECT_URL,
            }
        )
        return response.json()["access_token"]

    @staticmethod
    def get_email(access_token: str) -> str:
        response = requests.get(
            url="https://appleid.apple.com/auth/userinfo",
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-type': 'application/x-www-form-urlencoded',
                'charset': 'utf-8'
            }
        )
        email = response.json()['email']
        return email
