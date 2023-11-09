from ninja import Schema


class ExceptionSchema(Schema):
    error_code: str
    payload: dict | None
    status_code: int | None


class CustomException(Exception):
    def __init__(self, *args, **kwargs):
        if args:
            exception_dto = args[0]
            self.error_code = exception_dto.error_code
            self.payload = exception_dto.payload
            self.status_code = exception_dto.status_code
        else:
            self.error_code = kwargs.get('error_code', None)
            self.payload = kwargs.get('payload', None)
            self.status_code = kwargs.get('status_code', 400)
