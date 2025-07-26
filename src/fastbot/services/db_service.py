from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from FastBot.logger import Logger
from typing import List, Optional, Any


class DBService:
    def __init__(self, mongo_uri: str, db_name: str):
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(mongo_uri)
        self.db_name = db_name
        self.db: AsyncIOMotorDatabase = self.client[db_name]
        Logger.info(f"DBService initialized for database '{db_name}'")

    async def get_collection(
        self, collection_name: str
    ) -> Optional[AsyncIOMotorCollection]:
        return self.db[collection_name]

    async def create_collection(self, collection_name: str, **kwargs) -> bool:
        if collection_name in await self.db.list_collection_names():
            Logger.warning(f"Collection '{collection_name}' already exists")
            return False

        await self.db.create_collection(collection_name, **kwargs)
        Logger.info(f"Collection '{collection_name}' created successfully")
        return True

    async def drop_collection(self, collection_name: str) -> bool:
        if collection_name not in await self.db.list_collection_names():
            Logger.warning(f"Collection '{collection_name}' does not exist")
            return False

        await self.db.drop_collection(collection_name)
        Logger.info(f"Collection '{collection_name}' dropped successfully")
        return True

    async def list_collections(self) -> List[str]:
        collections = await self.db.list_collection_names()
        Logger.debug(f"Collections in database '{self.db_name}': {collections}")
        return collections

    async def close(self):
        self.client.close()
        Logger.info("DBService connection closed")
