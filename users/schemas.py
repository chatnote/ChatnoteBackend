from ninja import Schema


class UserSchema(Schema):
    id: int
    email: str
    profile_image: str | None

    @classmethod
    def from_instance(cls, user):
        return cls(id=user.id, email=user.email, profile_image=user.google_profile_image)


class SignUpParams(Schema):
    email: str
    password: str


class SignUpResponse(Schema):
    token: str
    user: UserSchema

    @classmethod
    def from_instance(cls, token, user):
        return cls(
            token=token,
            user=UserSchema(id=user.id, email=user.email, profile_image=user.google_profile_image)
        )


class LoginParams(Schema):
    email: str
    password: str


class LoginResponse(Schema):
    token: str


class GoogleSignupParams(Schema):
    code: str


class AppleSignupParams(Schema):
    code: str
