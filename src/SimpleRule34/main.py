import json
import xml.etree.ElementTree as ET

from .types import *


class Rule34BaseApi:
    _header = {'User-Agent': 'rule34-simple-api (Request)'}
    _url = f"https://api.rule34.xxx/index.php"

    def __init__(self, user_id: int, api_key: str, **kwargs):
        self._params = {
            'user_id': user_id,
            'api_key': api_key,
            'page': "dapi",
            'q': "index",
            **kwargs,
        }

    async def _get(self, json_: bool = True, **params) -> dict | str | None:
        """
        Raw request method

        :return:
        """

        # API allow boolean values only in 0/1 format, so we need to convert default boolean to this format
        json_parsed = 1 if json_ else 0

        async with aiohttp.ClientSession(headers=self._header) as session:
            async with session.get(self._url, params={**self._params, **params, 'json': json_parsed}) as response:
                if not response.ok and response.status not in [404, ]:
                    raise ApiException(await response.text())
                elif response.status == 404:
                    return None

                # Used for handling XML response
                if not json_:
                    return await response.text()

                try:
                    return await response.json()
                except json.decoder.JSONDecodeError:
                    raise ApiException(await response.text())


class Rule34PostApi(Rule34BaseApi):
    def __init__(self, user_id: int, api_key: str, **kwargs):
        super().__init__(user_id, api_key, **kwargs)
        self._params['s'] = "post"

    async def get(self, id: int) -> Rule34Post | None:
        """
        Method used to obtain a post by its ID

        :param id: Post ID
        :return: Post
        """

        post = await self._get(id=id)
        return Rule34Post(**post[0]) if post else None

    async def get_count(self, tags: list[str] = None) -> int:
        """
        Method used to get amount of all posts based on given tags.
        This value also includes deleted posts, actual amount of posts may be less.

        :param tags: List of tags
        :return: Amount of posts
        """

        if tags is None:
            tags = []

        xml_data = await self._get(json_=False, tags=" ".join(tags))
        if xml_data is None: return 0

        xml_root = ET.fromstring(xml_data)

        return int(xml_root.get('count'))

    async def get_list(self, amount: int = 1000, page: int = 0, tags: list[str] = None,
                       forbidden_tags: list[str] = None) -> list[Rule34Post]:
        """
        Method used to obtain list of posts based on given tags.

        :param amount: Amount of posts that will be searched with this request
        :param page:  Page number
        :param tags: List of tags
        :param forbidden_tags: List of tags posts with whom will be removed from list. When you specify forbidden tags returned amount of posts may be less than specified in amount value.
        :return: List of posts
        """

        if tags is None:
            tags = []
        if forbidden_tags is None:
            forbidden_tags = []

        if amount > 1000:
            raise ValueError(f"The max size of request is 1000 when you tried to request {amount}")

        raw_list = await self._get(limit=amount, pid=page, tags=" ".join(tags))
        if raw_list is None: return []

        post_list = [Rule34Post(**data) for data in raw_list]

        # Fast return if not sort is needed
        if len(forbidden_tags) < 1:
            return post_list

        sorted_post_list = []
        for post in post_list:
            if any(tag in forbidden_tags for tag in post.tags):
                pass
            else:
                sorted_post_list.append(post)

        return sorted_post_list


class Rule34CommentsApi(Rule34BaseApi):
    def __init__(self, user_id: int, api_key: str, **kwargs):
        super().__init__(user_id, api_key, **kwargs)
        self._params['s'] = "comment"

    async def get(self, post_id: int) -> list[Rule34Comment]:
        """
        Method used to obtain list of comments based on given post id.

        :param post_id: Post ID
        :return: List of comments
        """

        xml_data = await self._get(post_id=post_id, json_=False)
        if xml_data is None: return []

        xml_root = ET.fromstring(xml_data)

        return [Rule34Comment(**comment_e.attrib) for comment_e in xml_root.findall("comment")]


class Rule34TagsApi(Rule34BaseApi):
    def __init__(self, user_id: int, api_key: str, **kwargs):
        super().__init__(user_id, api_key, **kwargs)
        self._params['s'] = "tag"

    async def get(self, id: int) -> Rule34Tag | None:
        """
        Method used to obtain a tag data by its ID

        :param id: Tag ID
        :return: Tag
        """

        xml_data = await self._get(id=id, json_=False)
        if xml_data is None: return None

        xml_root = ET.fromstring(xml_data)

        raw_tag_data = xml_root.find("tag")
        if raw_tag_data is None:
            return None

        return Rule34Tag(**raw_tag_data.attrib)

    async def get_list(self, amount: int = 100, page: int = 0) -> list[Rule34Tag]:
        """
        Method used to obtain given amount of tags.

        :param amount: Amount of tags you want to obtain
        :return: List of tags
        """

        xml_data = await self._get(json_=False, limit=amount, pid=page)
        if xml_data is None: return []

        xml_root = ET.fromstring(xml_data)

        return [Rule34Tag(**tag_e.attrib) for tag_e in xml_root.findall("tag")]


class Rule34AutocompleteApi(Rule34BaseApi):
    def __init__(self, user_id: int, api_key: str, **kwargs):
        super().__init__(user_id, api_key, **kwargs)
        self._url = "https://api.rule34.xxx/autocomplete.php"
        self._params = {}

    async def search(self, text: str) -> list[Rule34Autocomplete]:
        return [Rule34Autocomplete(**data) for data in eval(await self._get(json_=False, q=text))]


class Rule34Api:
    def __init__(self, user_id: int, api_key: str, **kwargs):
        """
        After 13.07.2025 you need to use API key and user id to access the API.
        More info: https://discord.com/channels/336564284207267850/497927834241859586/1393885318477906021

        :param user_id: User ID
        :param api_key: API Key
        :param kwargs: Any other parameters that you want to pass to ANY requests. (No use cases, but may be used if any other global params will be added in the future)
        """
        self._user_id = user_id
        self._api_key = api_key

    @property
    def post(self) -> Rule34PostApi:
        return Rule34PostApi(user_id=self._user_id, api_key=self._api_key)

    @property
    def comments(self) -> Rule34CommentsApi:
        return Rule34CommentsApi(user_id=self._user_id, api_key=self._api_key)

    @property
    def tags(self) -> Rule34TagsApi:
        return Rule34TagsApi(user_id=self._user_id, api_key=self._api_key)

    @property
    def autocomplete(self) -> Rule34AutocompleteApi:
        return Rule34AutocompleteApi(user_id=self._user_id, api_key=self._api_key)
