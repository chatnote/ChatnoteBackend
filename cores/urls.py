from django.urls import *
from cores.apis import api, test_api, api_v2
from cores.views import *


urlpatterns = [
    path("api/v1/", api.urls),
    path("api/v2/", api_v2.urls),
    path("api/v1/test/", test_api.urls)
]
