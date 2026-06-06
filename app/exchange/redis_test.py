# test_redis.py
import asyncio
from redis import asyncio as aioredis

async def test_redis():
    try:
        # Attempt to connect
        redis = await aioredis.from_url(
            "redis://localhost:6379",  # Use 'redis' if running in Docker
            decode_responses=True
        )
        
        # Test write
        await redis.set("test_key", "Hello Redis!")
        
        # Test read
        value = await redis.get("dsps")
        
        print(f"✅ Redis connection successful!")
        print(f"   Wrote 'test_key', read back: {value}")
        
        # Clean up
        await redis.delete("test_key")
        await redis.aclose()
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_redis())
