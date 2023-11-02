from users.models import User


class SearchService:
    def __init__(self, user: User):
        self.user = user

    def search(self, keyword: str):
        pass