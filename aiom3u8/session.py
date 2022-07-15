from aiohttp.client import (
    ClientSession,
    ClientError
)


async def _get(session: ClientSession, url: str, retries: int, **kwargs):
    index = 0
    resp = None

    while index < retries:
        try:
            resp = await session.get(url, **kwargs)
            break
        except ClientError:
            index += 1

    return resp
