# BioLinkRemoverBot - All rights reserved
# © Graybots™. All rights reserved.

from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL

client = AsyncIOMotorClient(MONGO_URL)
db = client["BioLinkRemover"]
violation_col = db["violations"]

async def log_violation(chat_id: int, user_id: int, reason: str = "Violation"):
    await violation_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"reason": reason}},
        upsert=True
    )

async def clear_violations(chat_id: int, user_id: int):
    await violation_col.delete_one({"chat_id": chat_id, "user_id": user_id})

async def get_user_violations(chat_id: int, user_id: int):
    return await violation_col.find_one({
        "chat_id": chat_id,
        "user_id": user_id
    })
