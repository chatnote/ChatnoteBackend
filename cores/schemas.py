from ninja import Schema


class OriginalContext(Schema):
    id: str  # {url}
    user_id: int
    content_type: str
    title: str
    text: str
    text_hash: str  # original text parsing 로직을 바꾸면 hash 값 업데이트

    @classmethod
    def from_dict(cls, item: dict):
        return cls(
            id=item['id'],
            user_id=item['user_id'],
            content_type=item['content_type'],
            title=item['title'],
            text=item['text'],
            text_hash=item['text_hash']
        )


class ChunkedContext(Schema):
    id: str
    original_id: str
    user_id: int
    content_type: str
    text: str  # original text가 바뀔 때만 업데이트
    vector: str
    url: str
