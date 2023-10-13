import orjson
from django.conf import settings
from ninja.parser import Parser

from cores.auths import GlobalAuth
from cores.exception import CustomException
from ninja import NinjaAPI


class ORJSONParser(Parser):
    def parse_body(self, request):
        return orjson.loads(request.body)


api = NinjaAPI(
    version="1.0.0",
    parser=ORJSONParser(),
    auth=GlobalAuth(),
    docs_url="/docs" if settings.ENV != "prod" else None,
)


@api.exception_handler(CustomException)
def custom_exception(request, exc):
    return api.create_response(
        request,
        {"error_code": exc.error_code, "payload": exc.payload},
        status=exc.status_code,
    )
