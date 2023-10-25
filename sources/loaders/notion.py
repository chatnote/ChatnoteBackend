import hashlib
import logging
from typing import List

import requests
from django.utils.functional import cached_property
from tqdm import tqdm

from cores.enums import CustomEnum
from sources.schemas import OriginalDocumentSchema, NotionPageSchema
from sources.enums import DataSourceEnum

logger = logging.getLogger(__name__)


class NotionBlockEnum(CustomEnum):
    PARAGRAPH = "paragraph"
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    BULLETED_LIST_ITEM = "bulleted_list_item"
    NUMBERED_LIST_ITEM = "numbered_list_item"
    TO_DO = "to_do"
    TOGGLE = "toggle"
    CHILD_PAGE = "child_page"
    UNSUPPORTED = "unsupported"
    BOOKMARK = "bookmark"
    DIVIDER = "divider"
    PDF = "pdf"
    IMAGE = "image"
    EMBED = "embed"
    VIDEO = "video"
    FILE = "file"
    SYNCED_BLOCK = "synced_block"
    TABLE_OF_CONTENTS = "table_of_contents"
    COLUMN = "column"
    EQUATION = "equation"
    LINK_PREVIEW = "link_preview"
    COLUMN_LIST = "column_list"
    QUOTE = "quote"
    BREADCRUMB = "breadcrumb"
    LINK_TO_PAGE = "link_to_page"
    CHILD_DATABASE = "child_database"
    TEMPLATE = "template"
    CALLOUT = "callout"
    CODE = "code"


class RichTextEnum(CustomEnum):
    TEXT = 'text'
    EQUATION = 'equation'
    MENTION = 'mention'


def get_hash(text: str) -> str:
    return hashlib.md5(bytes(text, encoding="utf-8")).hexdigest()


class NotionLoader:
    def __init__(self, user):
        self.user = user
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {user.notion_access_token}", "Notion-Version": "2022-06-28"}
        )
        self.unsupported_block_types = [
            NotionBlockEnum.BOOKMARK,
            NotionBlockEnum.DIVIDER,
            NotionBlockEnum.CHILD_DATABASE,
            NotionBlockEnum.TEMPLATE,
            NotionBlockEnum.UNSUPPORTED,
        ]

        self.supported_block_types = [
            NotionBlockEnum.PARAGRAPH,
            NotionBlockEnum.HEADING_1,
            NotionBlockEnum.HEADING_2,
            NotionBlockEnum.HEADING_3,
            NotionBlockEnum.BULLETED_LIST_ITEM,
            NotionBlockEnum.NUMBERED_LIST_ITEM,
            NotionBlockEnum.TO_DO,
            NotionBlockEnum.TOGGLE,
            NotionBlockEnum.CHILD_PAGE,
            NotionBlockEnum.BOOKMARK,
            NotionBlockEnum.DIVIDER,
            NotionBlockEnum.EQUATION,
            NotionBlockEnum.QUOTE,
            NotionBlockEnum.CODE,
            NotionBlockEnum.CALLOUT,
        ]

        self.support_rich_text_data_type = [
            RichTextEnum.TEXT,
            RichTextEnum.EQUATION
        ]

        self.body_params = {"page_size": 100}

    @cached_property
    def get_all_page_or_databases(self) -> List[dict]:
        # Get all pages
        pages_or_databases = []

        while True:
            response = self.session.post(
                "https://api.notion.com/v1/search",
                json=self.body_params,
            ).json()

            pages_or_databases += response['results']
            if not response["has_more"]:
                break
            else:
                self.body_params.update({"start_cursor": response["next_cursor"]})

        return pages_or_databases

    @cached_property
    def get_all_page(self) -> List[dict]:
        pages_or_databases = self.get_all_page_or_databases
        results = []
        if pages_or_databases:
            results = [item for item in pages_or_databases if item["object"] == "page"]

        return results

    def process_page(self, page) -> OriginalDocumentSchema:
        title = self.get_page_title(page)
        description = self.get_page_description(page)
        raw_content = ""

        blocks = self.get_page_all_blocks(page["id"])
        for block in blocks["results"]:
            block_type = block.get("type")
            if not block_type or block_type not in self.supported_block_types:
                continue

            block_data = block[block_type]
            if not block_data.get("rich_text"):
                continue

            for rich_text in block_data["rich_text"]:
                rich_text = self.process_rich_text(rich_text, block_type)
                if rich_text:
                    raw_content += rich_text

            if block.get("has_children", True):
                nested_content = self.process_nested_children(self.get_children_blocks(block["id"]), "", block_type)
                if nested_content:
                    raw_content += nested_content

            raw_content += "\n"

        if not title or not description or not raw_content:
            text = ""
            if title:
                text += f"{title}\n"
            if description:
                text += f"{description}\n"
            if raw_content:
                text += f"{raw_content}"

            return OriginalDocumentSchema(
                user_id=self.user.id,
                data_source_type=DataSourceEnum.notion,
                url=page["url"],
                title=title,
                text=text,
                text_hash=get_hash(text)
            )

    def overall_process(self, pages=None):
        notion_document_schemas = []

        if not pages:
            pages = self.get_all_page

        # Get all pages content
        for i, page in enumerate(tqdm(pages)):
            if page["object"] == "database":
                # TODO: Handle databases
                continue
            elif page["object"] == "page":
                notion_document = self.process_page(page)
                if notion_document:
                    notion_document_schemas.append(notion_document)

        return notion_document_schemas

    def process_nested_children(self, children_blocks, raw_content, block_type=None):
        results = children_blocks["results"] if children_blocks.get("results") else []

        for child in results:
            child_type = child.get("type")
            if child_type is None:
                continue

            child_data = child[child_type]

            if not child_data.get("rich_text"):
                continue

            for text in child_data["rich_text"]:
                rich_text = self.process_rich_text(text, block_type)
                if rich_text:
                    raw_content += rich_text

            if child_data.get("has_children", True):
                nested_content = self.process_nested_children(self.get_children_blocks(child["id"]), "", block_type)
                if nested_content:
                    raw_content += nested_content

        return raw_content

    def process_rich_text(self, rich_text, block_type=None):
        rich_text_type = rich_text.get("type")
        if rich_text_type not in self.support_rich_text_data_type:
            return ""

        if rich_text.get("plain_text"):
            if block_type == NotionBlockEnum.CODE:
                return f"```{rich_text['text']['content']}```"
            elif rich_text_type == RichTextEnum.EQUATION:
                return f"$${rich_text['equation']['expression']}$$"
            elif rich_text.get("href", None):
                # return f"<a href='{rich_text['href']}'>{rich_text['plain_text']}</a>"
                return ""
            else:
                return rich_text["plain_text"]
        return ""

    def get_children_blocks(self, block_id):
        try:
            return self.session.get(f"https://api.notion.com/v1/blocks/{block_id}/children").json()
        except Exception as e:
            logger.error(f"Error getting children for block {block_id}: {e}")
            return {}

    def get_page(self, page_id):
        return self.session.get(f"https://api.notion.com/v1/pages/{page_id}").json()

    def get_page_all_blocks(self, page_id):
        # page의 child block 구할 때와 block의 child block 을 구할 때, 같은 API를 사용한다

        results = []
        page_size = 100
        start_cursor = None

        query_params = f"page_size={page_size}"
        while True:
            if start_cursor:
                query_params = f"page_size={page_size}&start_cursor={start_cursor}"

            try:
                response = self.session.get(
                    f"https://api.notion.com/v1/blocks/{page_id}/children?{query_params}",
                ).json()
            except Exception as e:
                logger.error(f"Error getting page {page_id}: {e}", exc_info=True)
                continue

            if response.get('object') == 'error':
                logger.error(f"Error response 500 in page id : {page_id}")
                continue

            results += response['results']
            if not response["has_more"]:
                break
            else:
                start_cursor = response["next_cursor"]

        response['results'] = results

        return response
        # return self.session.get(f"https://api.notion.com/v1/blocks/{page_id}/children").json()

    @staticmethod
    def get_page_title(page: dict):
        properties = page["properties"]

        title_field = ""
        for k, v in properties.items():
            if v['type'] == "title":
                title_field = k

        title = ""
        if not title_field:
            return title

        try:
            titles = page["properties"][title_field]["title"]
            for _title in titles:
                title += _title['plain_text']
        except Exception as e:
            print(e)
            title = ""

        return title

    @staticmethod
    def get_page_description(page):
        description = ""
        properties = page["properties"]

        for k, v in properties.items():
            if v['type'] == 'rich_text':
                for rich_text_data in v['rich_text']:
                    description += rich_text_data['plain_text']
        return description

    @staticmethod
    def get_parent_id(p_or_d):
        page_id = p_or_d["parent"].get("page_id", None)
        if page_id:
            return page_id

        database_id = p_or_d["parent"].get("database_id", None)
        if database_id:
            return database_id

        return None  # workspace page

    @staticmethod
    def get_object_type(p_or_d):
        if p_or_d["object"] == "database":
            return "database"
        elif p_or_d["object"] == "page":
            return "page"

    @staticmethod
    def get_icon(p_or_d):
        icon = p_or_d["icon"]
        emoji = icon.get("emoji") if icon else None
        return emoji if emoji else "📄"

    def _get_subpage_counts(self, p_or_d_id_2_info, p_or_d_id, object_type):
        child_ids = p_or_d_id_2_info[p_or_d_id]["child_ids"]

        counts = 0  # database
        if object_type == "page":
            counts = 1

        if len(child_ids) != 0:
            for child_id in child_ids:
                info = p_or_d_id_2_info[child_id]
                if len(info["child_ids"]) == 0:
                    counts += 1
                else:
                    counts += self._get_subpage_counts(p_or_d_id_2_info, child_id, info["object_type"])
        return counts

    def get_pages_and_counts(self) -> List[NotionPageSchema]:
        pages = self.get_all_page
        page_id_2_info = {}

        for page in pages:
            page_id_2_info[page["id"]] = {
                "title": self.get_page_title(page),
                "parent_id": self.get_parent_id(page),
                "object_type": self.get_object_type(page),
                "icon": self.get_icon(page),
                "url": page["url"],
                "child_ids": []
            }
        for _id, _info in page_id_2_info.items():
            parent_id = _info["parent_id"]
            if parent_id:
                page_id_2_info[parent_id]["child_ids"].append(_id)

        results = []
        for p_or_d_id, info in page_id_2_info.items():
            results.append(NotionPageSchema(
                url=info["url"],
                page_id=p_or_d_id,
                title=info["title"],
                icon=info["icon"],
                is_workspace=False if info["parent_id"] else True
            ))
        return results

    def get_workspace_pages(self) -> List[NotionPageSchema]:
        notion_page_schemas = self.get_pages_and_counts()
        return [item for item in notion_page_schemas if item.is_workspace]
