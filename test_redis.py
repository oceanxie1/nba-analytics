"""Simple script to test Redis connection and caching."""
import sys
from app.cache import cache_manager

def test_redis():
    """Test Redis connection and basic operations."""
    print("🧪 Testing Redis Connection...")
    print("-" * 50)
    
    # Check if Redis is enabled
    if not cache_manager.enabled:
        print("❌ Redis is NOT enabled")
        print("   This could mean:")
        print("   1. Redis server is not running")
        print("   2. Redis library is not installed (pip install redis)")
        print("   3. Redis connection failed")
        return False
    
    print("✅ Redis is enabled and connected!")
    print(f"   Connection: {cache_manager.redis_client.connection_pool.connection_kwargs}")
    print()
    
    # Test basic operations
    print("🧪 Testing Cache Operations...")
    print("-" * 50)
    
    # Test SET
    test_key = "test:cache:key"
    test_value = {"message": "Hello Redis!", "number": 42}
    print(f"1. Setting cache key: {test_key}")
    result = cache_manager.set(test_key, test_value, ttl=60)
    if result:
        print("   ✅ SET successful")
    else:
        print("   ❌ SET failed")
        return False
    
    # Test GET
    print(f"2. Getting cache key: {test_key}")
    retrieved = cache_manager.get(test_key)
    if retrieved == test_value:
        print("   ✅ GET successful - value matches!")
        print(f"   Retrieved: {retrieved}")
    else:
        print("   ❌ GET failed or value mismatch")
        print(f"   Expected: {test_value}")
        print(f"   Got: {retrieved}")
        return False
    
    # Test DELETE
    print(f"3. Deleting cache key: {test_key}")
    result = cache_manager.delete(test_key)
    if result:
        print("   ✅ DELETE successful")
    else:
        print("   ❌ DELETE failed")
        return False
    
    # Verify deletion
    retrieved = cache_manager.get(test_key)
    if retrieved is None:
        print("   ✅ Verified: Key is deleted")
    else:
        print("   ❌ Key still exists after deletion")
        return False
    
    print()
    print("✅ All Redis tests passed!")
    return True

if __name__ == "__main__":
    success = test_redis()
    sys.exit(0 if success else 1)

