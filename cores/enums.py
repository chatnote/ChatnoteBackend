from enum import EnumMeta, Enum


class TextEnum(str, Enum):
    def __str__(self):
        return self.value

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)

    @classmethod
    def values(cls) -> list:
        return [i.value for i in cls]

    @classmethod
    def get_enum(cls, value: str):
        for _value in cls.values():
            if _value == value:
                return cls
        return None


class EnumDirectValueMeta(EnumMeta):
    def __getattribute__(cls, name: str) -> str:
        attribute = super().__getattribute__(name)

        if (not name.startswith("_")) and isinstance(attribute, cls):
            attribute = attribute.value
        return attribute


class CustomEnum(TextEnum, metaclass=EnumDirectValueMeta):
    pass


class InvalidJwtErrorEnum(CustomEnum):
    invalid_jwt = 'invalid_jwt'


class ProviderEnum(CustomEnum):
    google = "google"
    kakao = "kakao"
    apple = "apple"


class ApiTagEnum(CustomEnum):
    core = 'core'
    user = 'user'
    document = 'document'
    source = 'source'
    chat = 'chat'
    test = 'test'
