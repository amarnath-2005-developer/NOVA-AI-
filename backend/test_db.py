import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def test():
    import certifi
    try:
        url = os.getenv("MONGODB_URL")
        print("Connecting to:", url)
        # Try with certifi
        client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        res = await client.admin.command('ping')
        print("SUCCESS with certifi:", res)
    except Exception as e:
        print("ERROR with certifi:", e)
        try:
            print("Retrying with tlsAllowInvalidCertificates=True...")
            client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
            res = await client.admin.command('ping')
            print("SUCCESS with invalid certs:", res)
        except Exception as e2:
            print("ERROR with invalid certs:", e2)

asyncio.run(test())
