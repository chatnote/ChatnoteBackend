from django.urls import *
from cores.apis import api, test_api
from cores.views import *


urlpatterns = [
    path("api/v1/", api.urls),
    path("api/v1/test/", test_api.urls)
]
