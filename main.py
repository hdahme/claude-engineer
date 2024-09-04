import asyncio
from chat.chat_manager import ChatManager

async def main():
    chat_manager = ChatManager()
    try:
        await chat_manager.run()
    finally:
        await chat_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())