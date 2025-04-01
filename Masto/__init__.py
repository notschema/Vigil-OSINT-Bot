from .masto import Masto, username_search, username_search_api, instance_search

async def username_search_async(username):
    async with Masto() as masto:
        await masto.username_search_api(username)
        return await masto.username_search(username)

__all__ = ['Masto', 'username_search', 'username_search_api', 'instance_search', 'username_search_async']
