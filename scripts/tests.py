from langchain.document_loaders import NotionDBLoader

from sources.enums import DataSourceEnum
from sources.loaders.notion import NotionLoader


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

    response = NotionSplitter.split(original_contexts)
    print(response)


def notion_loader():
    from llama_index import download_loader
    import os

    NotionPageReader = download_loader('NotionPageReader')

    integration_token = "secret_qbmtFSaUeYowlQhwkvypQM38jb5CO2UDurCKRaPta3a"
    page_ids = ["881433f7-5891-47c6-9563-6a052c6f4173"]
    reader = NotionPageReader(integration_token=integration_token)
    documents = reader.load_data(page_ids=page_ids)
    print(documents)


def notion_test():
    from users.models import User
    user = User.objects.get(email="ddr04014@gmail.com")
    notion_loader = NotionLoader(user)
    pages = notion_loader.get_all_page()
    print(len(pages))
    notion_document_schemas = NotionLoader(user).overall_process(pages)
    print(len(notion_document_schemas))


if __name__ == "__main__":
    import django

    django.setup()
    notion_test()
