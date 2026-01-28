import os
import typing
import re
import warnings

from enum import Enum
from pathlib import Path

import aiofiles
import aiohttp

from pydantic import BaseModel, field_validator, HttpUrl, Field

from .exceptions import ApiException
from .utils import get_file_type


class File(BaseModel):
    url: HttpUrl
    type: str = None

    def __init__(self, /, **data: typing.Any) -> None:
        super().__init__(**data)

        self.type = get_file_type(str(self.url))

    async def download(self, path: Path | str = "./rule34_downloads", file_name: Path | str = None) -> Path:
        if isinstance(path, str):
            path = Path(path)
        if isinstance(file_name, str):
            file_name = Path(file_name)

        # Create storage path
        path.mkdir(parents=True, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(str(self.url)) as response:
                if response.status != 200:
                    raise ApiException(f"Api returned status code {response.status} with message"
                                       f" {await response.text()}")

                original_file_name = Path(os.path.basename(str(self.url)))
                file_name = original_file_name if file_name is None else file_name
                if file_name.suffix != original_file_name.suffix:
                    warnings.warn("Provided file name suffix does not match original file name suffix. File can be corrupted.")

                save_path = path / file_name

                async with aiofiles.open(save_path, 'wb') as file:
                    await file.write(await response.read())

                return save_path


class Rule34Post(BaseModel):
    id: int
    owner: str | None
    status: str | None
    rating: str | None
    score: int | None

    preview_file: File  = Field(validation_alias="preview_url")
    sample_file: File  = Field(validation_alias="sample_url")
    file: File = Field(validation_alias="file_url")
    source: str | None

    width: int | None
    height: int | None
    hash: str | None
    image: str | None
    directory: int | None

    change: int | None
    parent_id: int | None
    has_notes: bool | None
    comment_count: int | None

    sample: bool | None
    sample_height: int | None
    sample_width: int | None

    tags: typing.List[str] | None

    @field_validator('tags', mode='before')
    @classmethod
    def split_tags(cls, v):
        if isinstance(v, str):
            return v.strip().split()
        return v

    @field_validator('preview_file', 'sample_file', 'file', mode='before', check_fields=False)
    @classmethod
    def wrap_in_file(cls, v):
        if isinstance(v, (str, HttpUrl)):
            return File(url=v)
        return v

    class Config:
        populate_by_name = True


class Rule34Comment(BaseModel):
    id: int
    post_id: int
    message: str = Field(alias="body")
    creator: str
    creator_id: int


class Rule34TagType(Enum):
    GENERAL = "0"
    ARTIST = "1"
    COPYRIGHT = "3"
    UNKNOWN = "2"
    CHARACTER = "4"
    META = "5"


class Rule34Tag(BaseModel):
    id: int
    type: Rule34TagType
    name: str
    count: int = Field(default_factory=int)
    ambiguous: bool


class Rule34Autocomplete(BaseModel):
    label: str
    value: str

    @property
    def count(self) -> int:
        return int(re.search(r'\((\d+)\)', self.label).group(1))
