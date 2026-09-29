"""
Unit Tests for LRU Cache and TTL Extension.
Validates correctness, edge cases, eviction ordering, TTL expiration, and thread safety.
"""

import time
import threading
import unittest
from src.lru_cache import Cache, LRUCache, TTLCache


class TestLRUCache(unittest.TestCase):
    """Test suite for core LRUCache requirements."""

    def test_assessment_example(self) -> None:
        """Verify the exact sequence given in the assessment specification."""
        cache = Cache(2)
        cache.put("A", 10)
        cache.put("B", 20)
        self.assertEqual(cache.get("A"), 10)    # Access "A" -> "A" becomes MRU, "B" is LRU
        cache.put("C", 30)                      # Exceeds capacity (2) -> Evicts LRU ("B")
        self.assertEqual(cache.get("B"), -1)    # "B" was evicted
        self.assertEqual(cache.get("C"), 30)    # "C" is present
        self.assertEqual(cache.get("A"), 10)    # "A" is present

    def test_capacity_validation(self) -> None:
        """Verify positive capacity constraint and type checks."""
        with self.assertRaises(ValueError):
            Cache(0)
        with self.assertRaises(ValueError):
            Cache(-1)
        with self.assertRaises(ValueError):
            Cache(-100)
        with self.assertRaises(TypeError):
            Cache("2")  # type: ignore
        with self.assertRaises(TypeError):
            Cache(2.5)  # type: ignore
        with self.assertRaises(TypeError):
            Cache(True)  # type: ignore

    def test_get_non_existent_key(self) -> None:
        """Non-existent keys must return -1."""
        cache = Cache(3)
        self.assertEqual(cache.get("non_existent"), -1)
        self.assertEqual(cache.get(404), -1)

    def test_put_update_existing_key(self) -> None:
        """Updating an existing key must overwrite value without increasing cache size."""
        cache = Cache(2)
        cache.put("A", 100)
        cache.put("B", 200)
        self.assertEqual(len(cache), 2)

        # Update existing key "A"
        evicted = cache.put("A", 999)
        self.assertIsNone(evicted)
        self.assertEqual(cache.get("A"), 999)
        self.assertEqual(len(cache), 2)

        # Now "B" is LRU; adding "C" should evict "B", not "A"
        evicted = cache.put("C", 300)
        self.assertEqual(evicted, ("B", 200))
        self.assertEqual(cache.get("B"), -1)
        self.assertEqual(cache.get("A"), 999)
        self.assertEqual(cache.get("C"), 300)

    def test_capacity_one(self) -> None:
        """Boundary test: capacity = 1."""
        cache = Cache(1)
        cache.put("X", 1)
        self.assertEqual(cache.get("X"), 1)

        evicted = cache.put("Y", 2)
        self.assertEqual(evicted, ("X", 1))
        self.assertEqual(cache.get("X"), -1)
        self.assertEqual(cache.get("Y"), 2)

    def test_strict_lru_ordering(self) -> None:
        """Test intricate access patterns and verify MRU-to-LRU internal order."""
        cache = Cache(3)
        cache.put(1, "one")
        cache.put(2, "two")
        cache.put(3, "three")
        # Current order: [3, 2, 1]

        self.assertEqual(cache.keys(), [3, 2, 1])

        # Touch 1 -> becomes MRU: [1, 3, 2]
        self.assertEqual(cache.get(1), "one")
        self.assertEqual(cache.keys(), [1, 3, 2])

        # Touch 2 -> becomes MRU: [2, 1, 3]
        self.assertEqual(cache.get(2), "two")
        self.assertEqual(cache.keys(), [2, 1, 3])

        # Insert 4 -> evicts LRU (3): [4, 2, 1]
        evicted = cache.put(4, "four")
        self.assertEqual(evicted, (3, "three"))
        self.assertEqual(cache.keys(), [4, 2, 1])
        self.assertEqual(cache.get(3), -1)

    def test_peek_does_not_alter_lru(self) -> None:
        """peek() should retrieve values without promoting the key to MRU."""
        cache = Cache(2)
        cache.put("A", 1)
        cache.put("B", 2)
        # Order: [B, A] -> A is LRU

        self.assertEqual(cache.peek("A"), 1)
        # Order must remain: [B, A]
        self.assertEqual(cache.keys(), ["B", "A"])

        # Inserting C must evict A (not B)
        evicted = cache.put("C", 3)
        self.assertEqual(evicted, ("A", 1))
        self.assertEqual(cache.get("A"), -1)
        self.assertEqual(cache.get("B"), 2)

    def test_delete_and_clear(self) -> None:
        """Test explicit deletion and clearing."""
        cache = Cache(3)
        cache.put("k1", "v1")
        cache.put("k2", "v2")

        self.assertTrue(cache.delete("k1"))
        self.assertFalse(cache.delete("k1"))  # Already deleted
        self.assertEqual(cache.get("k1"), -1)
        self.assertEqual(len(cache), 1)

        cache.clear()
        self.assertEqual(len(cache), 0)
        self.assertEqual(cache.get("k2"), -1)

    def test_various_key_types(self) -> None:
        """Cache must support various hashable key and value types."""
        cache = Cache(3)
        cache.put(42, "integer_key")
        cache.put(("coord", 1, 2), "tuple_key")
        cache.put("str_key", [1, 2, 3])

        self.assertEqual(cache.get(42), "integer_key")
        self.assertEqual(cache.get(("coord", 1, 2)), "tuple_key")
        self.assertEqual(cache.get("str_key"), [1, 2, 3])

    def test_thread_safety(self) -> None:
        """Concurrent reader and writer threads must not produce race conditions."""
        cache = Cache(50, thread_safe=True)
        errors = []

        def worker(thread_id: int) -> None:
            try:
                for i in range(100):
                    cache.put(f"key_{thread_id}_{i}", i)
                    val = cache.get(f"key_{thread_id}_{i}")
                    if val != -1 and val != i:
                        errors.append(f"Mismatch: got {val}, expected {i}")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")
        self.assertLessEqual(len(cache), 50)


class TestTTLCache(unittest.TestCase):
    """Test suite for optional TTL/expiration support."""

    def test_lazy_ttl_expiration(self) -> None:
        """Items must expire after their TTL and return -1 on get()."""
        ttl_cache = TTLCache(capacity=3)
        ttl_cache.put("short_lived", "data", ttl=0.1)
        ttl_cache.put("long_lived", "permanent", ttl=2.0)

        # Before expiration
        self.assertEqual(ttl_cache.get("short_lived"), "data")
        self.assertEqual(ttl_cache.get("long_lived"), "permanent")

        # Sleep past short_lived TTL
        time.sleep(0.15)

        # short_lived has expired
        self.assertEqual(ttl_cache.get("short_lived"), -1)
        # long_lived is still valid
        self.assertEqual(ttl_cache.get("long_lived"), "permanent")

    def test_ttl_update_renews_expiration(self) -> None:
        """Updating an existing key with a new TTL extends its expiry."""
        ttl_cache = TTLCache(capacity=2)
        ttl_cache.put("item", "v1", ttl=0.1)

        time.sleep(0.05)
        # Renew with 0.5s TTL
        ttl_cache.put("item", "v2", ttl=0.5)

        time.sleep(0.1)  # past original 0.1s
        # Must still be alive due to renewal
        self.assertEqual(ttl_cache.get("item"), "v2")

    def test_proactive_cleanup_expired(self) -> None:
        """cleanup_expired() must actively purge all expired entries."""
        ttl_cache = TTLCache(capacity=5)
        ttl_cache.put("e1", 1, ttl=0.05)
        ttl_cache.put("e2", 2, ttl=0.05)
        ttl_cache.put("keep", 3, ttl=5.0)

        time.sleep(0.08)
        purged_count = ttl_cache.cleanup_expired()
        self.assertEqual(purged_count, 2)
        self.assertEqual(len(ttl_cache), 1)
        self.assertEqual(ttl_cache.get("keep"), 3)

    def test_get_remaining_ttl(self) -> None:
        """get_remaining_ttl() returns positive remaining seconds or -1 if expired."""
        ttl_cache = TTLCache(capacity=2)
        ttl_cache.put("temp", "val", ttl=1.0)
        remaining = ttl_cache.get_remaining_ttl("temp")
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 0.0)
        self.assertLessEqual(remaining, 1.0)

        time.sleep(1.05)
        self.assertEqual(ttl_cache.get_remaining_ttl("temp"), -1)


if __name__ == "__main__":
    unittest.main()
