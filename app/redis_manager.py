import asyncio

from redis.asyncio import Redis as RedisAsync
from app.cred_loader import cred_loader
from traceback import print_exc
import json, pickle
from app.ws_connection_manager import ws_manager

class RedisChatManager():

    def __init__(self):
        # Connect to Redis
        self.HOST = cred_loader.redis_creds['host']
        self.PORT = cred_loader.redis_creds['port']
        self.DB = cred_loader.redis_creds['db']

    async def connect_redis(self):
       # creates redis instance and make it an instace attr when this method is called
        self.redis = RedisAsync(
            host=self.HOST,
            port=self.PORT,
            db=self.DB,
            decode_responses=False
        )
        # Test the connection
        await self.redis.ping()
        self.pubsub = self.redis.pubsub()
        print("Connected to Redis successfully!")

    async def get_value(self, key: str):
        
        value = await self.redis.get(key)
        if value is None:
            # print("Value not found")
            return False
        # print("Value retrieved successfully")
        
        value = pickle.loads(value)
        return value
    
    async def set_value(self, key: str, value):
        try:

            value = pickle.dumps(value)
            await self.redis.set(key, value)
            return True
        
        except Exception as e:
            print_exc()
            return False        

    async def set_online(self, user_id):
        active_connections = await self.get_value("active_connections")
        
        if active_connections:
            active_connections.add(user_id)
        else:
            active_connections = set()
            active_connections.add(user_id)
            
        await self.set_value('active_connections', active_connections)
        await self.pubsub.subscribe(f"chat_{user_id}")
        print("Added online", active_connections)

    async def set_offline(self, user_id):
        active_connections = await self.get_value("active_connections")
        
        if type(active_connections) == set and user_id in active_connections:
            active_connections.remove(user_id)

        await self.set_value('active_connections', active_connections)
        await self.pubsub.unsubscribe(f"chat_{user_id}")

    async def publish(self, channel: str, message: str):
        try:
            
            await self.redis.publish(channel, message)
            return True
        
        except Exception as e:
            print_exc()
            return False
    
    async def listen_messages(self, user_id, websocket):
        """Continuously listen for messages published to this user's channel."""
        async for message in self.pubsub.listen():
            # print(message)
            if message["type"] == "message" and message["channel"].decode('utf-8') == f"chat_{user_id}":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                    data = json.loads(data)
                    await websocket.send_json(data)