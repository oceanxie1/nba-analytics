"""Benchmark script to measure cache performance."""
import time
import requests
import statistics
from typing import List

API_BASE = "http://localhost:8000"

def benchmark_endpoint(endpoint: str, iterations: int = 10) -> dict:
    """Benchmark an endpoint with and without cache.
    
    Args:
        endpoint: API endpoint to test (e.g., "/players/1/features?season=2023-24")
        iterations: Number of requests to make
        
    Returns:
        Dictionary with timing statistics
    """
    url = f"{API_BASE}{endpoint}"
    
    # First request (cache miss - warms the cache)
    print(f"🔥 Warming cache...")
    start = time.time()
    response = requests.get(url)
    first_request_time = time.time() - start
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return None
    
    # Clear cache for accurate measurement
    print(f"🗑️  Clearing cache...")
    requests.post(f"{API_BASE}/cache/stats/reset")
    
    # Test without cache (first request)
    print(f"📊 Testing WITHOUT cache ({iterations} requests)...")
    times_without_cache = []
    for i in range(iterations):
        start = time.time()
        requests.get(url)
        elapsed = time.time() - start
        times_without_cache.append(elapsed)
        print(f"  Request {i+1}: {elapsed*1000:.2f}ms")
    
    # First request creates cache, so use subsequent requests
    avg_without_cache = statistics.mean(times_without_cache[1:]) if len(times_without_cache) > 1 else times_without_cache[0]
    
    # Test with cache (subsequent requests)
    print(f"\n📊 Testing WITH cache ({iterations} requests)...")
    times_with_cache = []
    for i in range(iterations):
        start = time.time()
        requests.get(url)
        elapsed = time.time() - start
        times_with_cache.append(elapsed)
        print(f"  Request {i+1}: {elapsed*1000:.2f}ms")
    
    avg_with_cache = statistics.mean(times_with_cache)
    
    # Calculate improvements
    speedup = avg_without_cache / avg_with_cache if avg_with_cache > 0 else 0
    time_saved = (avg_without_cache - avg_with_cache) * 1000  # in milliseconds
    improvement_percent = ((avg_without_cache - avg_with_cache) / avg_without_cache * 100) if avg_without_cache > 0 else 0
    
    return {
        "endpoint": endpoint,
        "iterations": iterations,
        "avg_without_cache_ms": round(avg_without_cache * 1000, 2),
        "avg_with_cache_ms": round(avg_with_cache * 1000, 2),
        "speedup_factor": round(speedup, 2),
        "time_saved_ms": round(time_saved, 2),
        "improvement_percent": round(improvement_percent, 2),
        "min_with_cache_ms": round(min(times_with_cache) * 1000, 2),
        "max_with_cache_ms": round(max(times_with_cache) * 1000, 2),
        "min_without_cache_ms": round(min(times_without_cache) * 1000, 2),
        "max_without_cache_ms": round(max(times_without_cache) * 1000, 2),
    }


def main():
    """Run cache benchmarks."""
    print("=" * 60)
    print("🚀 CACHE PERFORMANCE BENCHMARK")
    print("=" * 60)
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Server is not responding. Make sure FastAPI is running.")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print(f"   Make sure FastAPI is running on {API_BASE}")
        return
    
    # Check cache status
    try:
        stats_response = requests.get(f"{API_BASE}/cache/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            if not stats.get("cache_enabled"):
                print("⚠️  Warning: Cache is not enabled!")
                print("   Make sure Redis is running and redis library is installed.")
        else:
            print("⚠️  Could not check cache status")
    except Exception as e:
        print(f"⚠️  Could not check cache status: {e}")
    
    print()
    
    # Benchmark endpoints
    endpoints = [
        "/players/1/features?season=2023-24",
        "/teams/1/stats/2023-24",
    ]
    
    results = []
    for endpoint in endpoints:
        print(f"\n{'='*60}")
        print(f"Testing: {endpoint}")
        print(f"{'='*60}")
        result = benchmark_endpoint(endpoint, iterations=10)
        if result:
            results.append(result)
        print()
    
    # Summary
    if results:
        print("\n" + "=" * 60)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 60)
        print()
        
        for result in results:
            print(f"Endpoint: {result['endpoint']}")
            print(f"  Without Cache: {result['avg_without_cache_ms']}ms")
            print(f"  With Cache:    {result['avg_with_cache_ms']}ms")
            print(f"  Speedup:       {result['speedup_factor']}x faster")
            print(f"  Time Saved:    {result['time_saved_ms']}ms per request")
            print(f"  Improvement:   {result['improvement_percent']}%")
            print()
        
        # Get API stats
        try:
            stats_response = requests.get(f"{API_BASE}/cache/stats")
            if stats_response.status_code == 200:
                stats = stats_response.json().get("statistics", {})
                print("=" * 60)
                print("📈 LIVE CACHE STATISTICS")
                print("=" * 60)
                print(f"Total Requests: {stats.get('total_requests', 0)}")
                print(f"Cache Hits:     {stats.get('hits', 0)}")
                print(f"Cache Misses:   {stats.get('misses', 0)}")
                print(f"Hit Rate:       {stats.get('hit_rate_percent', 0)}%")
                print(f"Avg (with cache):    {stats.get('avg_response_time_with_cache_ms', 0)}ms")
                print(f"Avg (without cache): {stats.get('avg_response_time_without_cache_ms', 0)}ms")
                print(f"Speedup Factor:      {stats.get('speedup_factor', 0)}x")
        except Exception as e:
            print(f"Could not fetch live stats: {e}")


if __name__ == "__main__":
    main()

