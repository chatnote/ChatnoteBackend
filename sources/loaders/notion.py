import hashlib
import logging
from time import sleep
from typing import List

import requests
from tqdm import tqdm

from cores.enums import CustomEnum
from sources.schemas import NotionPageSchema, NotionSearchPageSchema

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


class NotionUserLoader:
    def __init__(self, user):
        self.user = user

    def get_email(self):
        email = ""
        response = requests.get(
            url="https://api.notion.com/v1/users",
            headers={
                "Authorization": f"Bearer {self.user.notion_access_token}", "Notion-Version": "2022-06-28"
            }
        ).json()
        if "results" in response:
            for data in response["results"]:
                if data["type"] == "person":
                    email = data["person"]["email"]
                    break

        return email


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
            # NotionBlockEnum.EQUATION,
            NotionBlockEnum.QUOTE,
            # NotionBlockEnum.CODE,
            NotionBlockEnum.CALLOUT,
        ]

        self.support_rich_text_data_type = [
            RichTextEnum.TEXT,
            # RichTextEnum.EQUATION
        ]

    def search(self, keyword: str, offset: int = 0, limit: int = 15) -> List[NotionSearchPageSchema]:
        body_params = {
            "query": f"{keyword}",
            "sort": {
                "direction": "descending",
                "timestamp": "last_edited_time"
            },
            "page_size": 50
        }
        response = self.session.post(
            "https://api.notion.com/v1/search",
            json=body_params
        ).json()

        notion_search_page_schemas = [
            NotionSearchPageSchema(
                url=self.get_url(p_or_d),
                title=self.get_page_title(p_or_d),
                icon=self.get_icon(p_or_d)
            ) for p_or_d in response["results"][offset: offset + limit]
        ]
        return notion_search_page_schemas

    def get_all_page_or_databases(self) -> List[dict]:
        # Get all pages
        pages_or_databases = []

        body_params = {
            "page_size": 100
        }
        while True:
            response = self.session.post(
                "https://api.notion.com/v1/search",
                json=body_params,
            ).json()

            pages_or_databases += response['results']
            if not response["has_more"]:
                break
            else:
                body_params.update({"start_cursor": response["next_cursor"]})

        return pages_or_databases

    def get_all_page(self) -> List[dict]:
        pages_or_databases = self.get_all_page_or_databases()
        results = []
        if pages_or_databases:
            results = [item for item in pages_or_databases if item["object"] == "page"]

        return results

    def overall_process(self, pages=None):
        notion_page_schemas = []

        # Get all pages content
        for page in tqdm(pages):
            if page["object"] == "page":
                processed_page = self.process_page(page)
                sleep(0.5)
                if processed_page:
                    notion_page_schemas.append(processed_page)

        return notion_page_schemas

    def process_page(self, page) -> NotionPageSchema:
        title = self.get_page_title(page)
        description = self.get_page_description(page)
        page_id = self.get_id(page)
        icon = self.get_icon(page)
        is_workspace = self.is_workspace_page(page)

        raw_content = ""
        page_blocks = self.get_blocks(page_id=page["id"])
        for block in page_blocks:
            block_type = block.get("type")
            if block_type not in self.supported_block_types:
                continue

            block_data = block[block_type]
            if not block_data.get("rich_text"):
                continue

            for rich_text_data in block_data["rich_text"]:
                rich_text = self.process_rich_text(rich_text_data)
                if rich_text:
                    raw_content += f"{rich_text}\n"

            if block.get("has_children", True):
                children_blocks = self.get_blocks(page_id=block["id"])
                nested_content = self.process_nested_blocks(children_blocks, "\t")
                if nested_content:
                    raw_content += nested_content

        if title or description or raw_content:
            return NotionPageSchema(
                url=page["url"],
                page_id=page_id,
                title=title,
                description=description,
                text=raw_content,
                text_hash=get_hash(raw_content),
                icon=icon,
                is_workspace=is_workspace
            )

    def get_children_blocks(self, block_id):
        try:
            return self.session.get(f"https://api.notion.com/v1/blocks/{block_id}/children").json()["results"]
        except Exception as e:
            logger.error(f"Error getting children for block {block_id}: {e}")
            return []

    def process_rich_text(self, rich_text_data):
        rich_text_type = rich_text_data.get("type")
        if rich_text_type not in self.support_rich_text_data_type:
            return ""

        if rich_text_data.get("plain_text"):
            if rich_text_type == RichTextEnum.EQUATION:
                # return f"$${rich_text['equation']['expression']}$$"
                return ""
            elif rich_text_data.get("href", None):
                # return f"<a href='{rich_text['href']}'>{rich_text['plain_text']}</a>"
                return ""
            else:
                return rich_text_data["plain_text"]
        return ""

    def get_blocks(self, page_id: str):
        # page의 child block 구할 때와 block의 child block 을 구할 때, 같은 API를 사용한다

        block_list = []
        page_size = 100
        start_cursor = None

        query_params = f"page_size={page_size}"
        while True:
            if start_cursor:
                query_params = f"page_size={page_size}&start_cursor={start_cursor}"

            try:
                response = self.session.get(
                    f"https://api.notion.com/v1/blocks/{page_id}/children?{query_params}",
                )
            except Exception as e:
                print(f"Exception from get blocks of page_id {page_id}, {e}")
                break

            if response.status_code == 200:
                data = response.json()
                block_list += data['results']
                if not data["has_more"]:
                    break
                else:
                    start_cursor = data["next_cursor"]
            else:
                print(f"Exception from get blocks of page_id {page_id}, {response.json()}")
                break

        return block_list

    def process_nested_blocks(self, children_blocks, appended_str):
        raw_content = ""

        for child in children_blocks:
            child_type = child.get("type")
            child_data = child[child_type]

            if not child_data.get("rich_text"):
                continue

            for rich_text_data in child_data["rich_text"]:
                rich_text = self.process_rich_text(rich_text_data)
                if rich_text:
                    raw_content += f"{appended_str}{rich_text}\n"

            if child_data.get("has_children", True):
                children_blocks = self.get_blocks(page_id=child["id"])
                nested_content = self.process_nested_blocks(children_blocks, f"{appended_str}\t")
                if nested_content:
                    raw_content += nested_content
        return raw_content

    def get_page(self, page_id: str):
        response = self.session.get(
            f"https://api.notion.com/v1/pages/{page_id}"
        ).json()
        return response

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
            title = ""

        return title

    @staticmethod
    def get_page_description(page):
        description = ""
        properties = page["properties"]

        for k, v in properties.items():
            plain_text = ""
            if v['type'] == 'rich_text':
                for rich_text_data in v['rich_text']:
                    plain_text += rich_text_data['plain_text']
            elif v['type'] == 'multi_select':
                for multi_select_data in v['multi_select']:
                    plain_text += f"{multi_select_data['name']}, "

            if plain_text:
                description += f"{k}: {plain_text}\n"

        return description

    @staticmethod
    def is_workspace_page(p_or_d):
        is_workspace = p_or_d["parent"].get("workspace", None)

        if is_workspace:
            return True
        else:
            return False

    @staticmethod
    def get_icon(p_or_d):
        icon = p_or_d["icon"]
        emoji = icon.get("emoji") if icon else None
        return emoji if emoji else "📄"

    @staticmethod
    def get_id(p_or_d):
        return p_or_d["id"]

    @staticmethod
    def get_url(p_or_d):
        return p_or_d["url"]

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

    def get_all_page_schemas(self, pages: list = None) -> List[NotionPageSchema]:
        results = []
        if not pages:
            pages = self.get_all_page()
        for page in pages:
            results.append(NotionPageSchema(
                url=page["url"],
                page_id=page["id"],
                title=self.get_page_title(page),
                icon=self.get_icon(page),
                is_workspace=True if self.is_workspace_page(page) else False
            ))
        return results
