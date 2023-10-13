from sources.enums import DataSourceEnum


def test_splitter():
    from sources.schemas import OriginalDocumentSchema
    from sources.services import NotionSplitter
    from sources.loaders.notion import NotionLoader
    from users.models import User

    user = User.objects.get(email='ddr04014@gmail.com')

    # original_contexts = NotionLoader(user).overall_process()
    # print(original_contexts)

    document = user.originaldocument_set.get(url="https://www.notion.so/7938cc8f2a6d431287449ddaeabb970b")
    original_contexts = [
        OriginalDocumentSchema(
            user_id=user.id,
            data_source_type=DataSourceEnum.notion,
            url=document.url,
            title=document.title,
            text=document.text,
            text_hash=document.text_hash
        )
    ]

    response = NotionSplitter.split_by_token(original_contexts)
    print(response)


if __name__ == "__main__":
    import django

    django.setup()
    test_splitter()
