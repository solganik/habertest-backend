import json
import aiohttp


async def theoretically_fulfill(resource_manager, data):
    rm_ep = resource_manager['endpoint']
    url = f"http://{rm_ep}/fulfill/theoretically"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json.dumps(data), timeout=5) as resp:
                result = await resp.json()
                if resp.status != 200:
                    raise Exception(f"cant theoretically fulfill: res: {result}")
                return resource_manager
    except:
        raise ConnectionError(f"Couldnt connect to resource_manager {rm_ep}")


async def allocate(rm_ep, data):
    url = f"http://{rm_ep}/fulfill/now"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=json.dumps(data)) as resp:
            result = await resp.json()
            if resp.status != 200:
                raise Exception(f"Error allocating on ep {rm_ep} with data {data}: {result}")
            return result


async def deallocate(resource_name, manager_ep):
    url = f'http://{manager_ep}/deallocate/{resource_name}'
    async with aiohttp.ClientSession() as session:
        async with session.delete(url) as resp:
            result = await resp.json()
            if resp.status != 200:
                raise Exception(f"Error deallocating resource {resource_name} on {manager_ep}: {result}")
            return result


async def check_status(allocation_id, manager_ep):
    url = f'http://{manager_ep}/allocations/{allocation_id}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            result = await resp.json()
            if resp.status != 200:
                raise Exception(f"Error getting status of {allocation_id} ep {manager_ep}: {result}")
            return result
