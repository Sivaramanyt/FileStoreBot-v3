import logging
from pyrogram import Client
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class FileStoreBot(Client):
    def __init__(self):
        super().__init__(
            "FileStoreBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins={"root": "plugins"}
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        logger.info(f"Bot started as @{me.username}")
        print(f"🤖 Bot started as @{me.username}")

    async def stop(self):
        await super().stop()
        logger.info("Bot stopped")
        print("🛑 Bot stopped")

if __name__ == "__main__":
    bot = FileStoreBot()
    bot.run()
