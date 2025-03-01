"""
redis singleton
"""
import json
import os
import time
import uuid

import redis
import asyncio_redis


# pylint: disable=R0903
class RedisClient:
    """
    exposes a redis connection
    """

    # pylint: disable=too-many-arguments
    def __init__(self, host, port, username, password, db=None):
        self._conn = None
        self._asyncconn = None
        self.host = host
        self.port = int(port)
        self.database = int(db)
        self.pool = redis.ConnectionPool(
            host=host, port=port, username=username, password=password, db=db
        )
        self._async = None

    @property
    def conn(self):
        """
        returns a redis connection
        """
        if not self._conn:
            self.__create_connection()
        return self._conn

    @property
    async def asyncconn(self):
        """
        return an async connection
        """
        if not self._asyncconn:
            await self.__create_asyncconnection()
        return self._asyncconn

    async def __create_asyncconnection(self):
        """
        instantiate an async connection
        """
        self._asyncconn = await asyncio_redis.Connection.create(
            host=self.host,
            port=self.port
        )

    def __create_connection(self):
        self._conn = redis.Redis(connection_pool=self.pool)

    async def resource_managers(self, resource_manager=None):
        conn = await self.asyncconn
        if resource_manager:
            res = await conn.hget("resource_managers", resource_manager)
            return json.loads(res)
        res = dict()
        resource_managers = await conn.hgetall_asdict("resource_managers")
        for name, resource_manager_str in resource_managers.items():
            resource_manager = json.loads(resource_manager_str)
            res[name] = resource_manager
        return res

    async def allocations(self, allocation_id=None):
        conn = await self.asyncconn
        if allocation_id:
            allocations = await conn.hget("allocations", allocation_id)
            if not allocations:
                return None
            return json.loads(allocations)
        else:
            res = dict()
            allocations = await conn.hgetall_asdict("allocations")
            for id, allocation_str in allocations.items():
                res[id] = json.loads(allocation_str)
            return res

    async def save_request(self, request):
        conn = await self.asyncconn
        request['status'] = "received"
        request['expiration'] = int(time.time()) + 60
        await conn.hset('allocations', request['allocation_id'], json.dumps(request))


    async def save_fulfilled_request(self, allocation_id, resource_manager, allocation_result):
        hardware_details = list()
        for allocated_vm in allocation_result['info']:
            hardware_details.append(dict(
                ip=allocated_vm['net_ifaces'][0]['ip'],
                user=allocated_vm.get('user', None),
                password=allocated_vm.get('password', None),
                pem_key_string=allocated_vm.get('pem_key_string', None),
                keyfile_path=allocated_vm.get('key_file_path', None),
                resource_manager_ep=resource_manager['endpoint'],
                vm_id=allocated_vm['name']
            ))
        await self.update_status(allocation_id,
                                 resource_manager=resource_manager['endpoint'],
                                 hardware_details=hardware_details,
                                 result=allocation_result,
                                 status="success",
                                 expiration=int(time.time()) + 60,
                                 )

    async def update_status(self, allocation_id, **kwargs):
        conn = await self.asyncconn
        allocation = await self.allocations(allocation_id)
        allocation.update(kwargs)
        await conn.hset('allocations', allocation["allocation_id"], json.dumps(allocation))

    async def delete(self, key, fields):
        fields = fields if type(fields) is list else [fields]
        conn = await self.asyncconn
        await conn.hdel(key, fields)

    def resource_managers_sync(self):
        rms_raw = self.conn.hgetall("resource_managers")
        rms = dict()
        if rms_raw:
            for k, v in rms_raw.items():
                rm = json.loads(v)
                rms[k] = rm
        return rms

    def allocations_sync(self):
        redis_allocations_raw = self.conn.hgetall("allocations")
        redis_allocations = dict()
        for id, allocation_str in redis_allocations_raw.items():
            redis_allocations[id.decode()] = json.loads(allocation_str)
        return redis_allocations


REDIS = RedisClient(
    host=os.getenv("REDIS_HOST", "redis"),
    port=os.getenv("REDIS_PORT", "6379"),
    username="",  # os.getenv("REDIS_USER"),
    password="",  # os.getenv("REDIS_PASSWORD"),
    db=os.getenv("REDIS_DB", 0),
)
