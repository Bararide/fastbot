from motor.motor_asyncio import AsyncIOMotorClient
from models.user import User
from models.user_stats import UserStats
from src.FastBotLib.logger.logger import Logger
from typing import Optional


class AuthService:
    def __init__(self, mongo_uri: str, db_name: str):
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[db_name]
        self.users = self.db["users"]

    async def get_user(self, user_id: int) -> Optional[User]:
        Logger.info(f"Getting user: {user_id}")
        user = await self.users.find_one({"id": user_id})
        return User(**user) if user else None

    async def register_user(self, user_data: dict) -> User:
        if await self.users.find_one({"id": user_data["id"]}):
            raise ValueError("User already exists")

        user = User(**user_data)
        await self.users.insert_one(user.dict())
        Logger.info(f"New user registered: {user.id}")
        return user

    async def update_user(self, user_id: int, update_data: dict) -> bool:
        result = await self.users.update_one({"id": user_id}, {"$set": update_data})
        return result.modified_count > 0

    async def delete_user(self, user_id: int) -> bool:
        result = await self.users.delete_one({"id": user_id})
        return result.deleted_count > 0

    async def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        return UserStats(id=user_id)
