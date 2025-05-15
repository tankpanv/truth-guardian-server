import json


class ArticleContent:
    def __init__(self, id: int = 0, iid: int = 0, content: str = "", category: str = "", tags: str = "",
                 title: str = "", abstract: str = "", keywords: str = "", content_html: str = "",
                 image_url: str = "", image_url1: str = "", image_url2: str = "", image_url3: str = "",
                 origin_url: str = "", origin_source: str = "", read_count: str = "0", like_count: str = "0",
                 comment_count: str = "0", comment1: str = "", comment2: str = "", comment3: str = "",
                 comment1_count: str = "0", comment2_count: str = "0", comment3_count: str = "0",
                 author: str = "", timestamp: str = "", timestamp_out: str = "", author_url: str = "",
                 visibility: int = 1, creator_id: int = 0, creator: str = "", deleted_at: str = "",
                 created_at: str = "", updated_at: str = "", logo: str = "", genre: int = 0,
                 editor: int = 0, source: str = '', reship_url: str = "", url: str = "",
                 comment_data: str = "", uri: str = "", data: str = "", id_str: str = "", 
                 data_map: dict = None,image_list: list = []):
        if data_map is None:
            data_map = {}
        self.image_list = image_list
        self.id = id
        self.iid = iid
        self.content = content
        self.category = category
        self.tags = tags
        self.title = title
        self.abstract = abstract
        self.keywords = keywords
        self.content_html = content_html
        self.image_url = image_url
        self.image_url1 = image_url1
        self.image_url2 = image_url2
        self.image_url3 = image_url3
        self.origin_url = origin_url
        self.origin_source = origin_source
        self.read_count = str(read_count)
        self.like_count = str(like_count)
        self.comment_count = str(comment_count)
        self.comment1 = comment1
        self.comment2 = comment2
        self.comment3 = comment3
        self.comment1_count = str(comment1_count)
        self.comment2_count = str(comment2_count)
        self.comment3_count = str(comment3_count)
        self.author = author
        self.timestamp = timestamp
        self.timestamp_out = timestamp_out
        self.author_url = author_url
        self.visibility = visibility
        self.creator_id = creator_id
        self.creator = creator
        self.deleted_at = deleted_at
        self.created_at = created_at
        self.updated_at = updated_at
        self.logo = logo
        self.genre = genre
        self.editor = editor
        self.source = source
        self.reship_url = reship_url
        self.url = url
        self.comment_data = comment_data
        self.uri = uri
        self.data = data
        self.id_str = id_str
        self.data_map = data_map
        self.webo_id=''

    def __repr__(self):
        return f"<ArticleContent(title={self.title}, author={self.author}, created_at={self.created_at})>"
    def to_json(self):
        """将 OriItem 对象转换为 JSON 格式的字符串"""
        return json.dumps(self.__dict__, ensure_ascii=False)
from typing import List
from dataclasses import dataclass, field

@dataclass
class Comment:
    user_id: str = ""
    source: str = ""
    username: str = ""
    content: str = ""
    like_count: int = 0
    comment_count: int = 0
    sub_comment: List['Comment'] = field(default_factory=list)

    def to_json(self):
        """将 Comment 实例转换为 JSON 格式的字典"""
        return {
            "user_id": self.user_id,
            "source": self.source,
            "username": self.username,
            "content": self.content,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "sub_comment": [sub.to_json() for sub in self.sub_comment]
        }

