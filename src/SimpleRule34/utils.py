FILE_TYPES = {
    'jpg': "photo",
    'jpeg': "photo",
    'png': "photo",

    'mp4': "video",
    'avi': "video",
    'mov': "video",
    'webm': "video",

    'gif': "animation",
}


async def get_file_size(url, session):
    async with session.head(url=url, allow_redirects=True) as response:
        if 'Content-Length' in response.headers:
            size = int(response.headers['Content-Length'])
            return size
        else:
            return None


def get_file_type(url) -> str | None:
    file_extension = url.split('.')[-1].lower()

    if file_extension not in FILE_TYPES.keys(): return None

    return FILE_TYPES[file_extension]


