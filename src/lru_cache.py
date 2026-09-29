"""
Least Recently Used (LRU) Cache Implementation with O(1) Operations
and Optional Time-To-Live (TTL) Expiration Support.

Data Structures:
- Hash Map (dict): Maps key -> Doubly Linked List Node for O(1) average lookup.
- Doubly Linked List (DLL): Maintains access ordering from Most Recently Used (MRU)
  at the head to Least Recently Used (LRU) at the tail. O(1) insertion, removal,
  and re-ordering.
"""

from __future__ import annotations
import threading
import time
from typing import Any, Optional


class Node:
    """Doubly Linked List node storing key-value pairs and optional expiration timestamp."""
    __slots__ = ("key", "value", "prev", "next", "expires_at")

    def __init__(
        self,
        key: Any = None,
        value: Any = None,
        expires_at: Optional[float] = None,
    ) -> None:
        self.key = key
        self.value = value
        self.expires_at = expires_at
        self.prev: Optional[Node] = None
        self.next: Optional[Node] = None

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        """Check if the node has passed its expiration timestamp."""
        if self.expires_at is None:
            return False
        now = time.time() if current_time is None else current_time
        return now > self.expires_at

    def __repr__(self) -> str:
        ttl_info = f", expires_at={self.expires_at}" if self.expires_at else ""
        return f"Node({self.key}: {self.value}{ttl_info})"


class LRUCache:
    """
    Least Recently Used (LRU) Cache.
    
    Guarantees:
    - O(1) average time complexity for both get() and put()
    - O(capacity) space complexity
    - Thread-safe operations via reentrant locking (optional, enabled by default)
    """

    def __init__(self, capacity: int, thread_safe: bool = True) -> None:
        if not isinstance(capacity, int) or isinstance(capacity, bool):
            raise TypeError(f"Capacity must be an integer, got {type(capacity).__name__}")
        if capacity <= 0:
            raise ValueError(f"Capacity must be a positive integer (> 0), got {capacity}")

        self.capacity = capacity
        self._map: dict[Any, Node] = {}
        self._thread_safe = thread_safe
        self._lock = threading.RLock() if thread_safe else None

        # Sentinel dummy nodes to eliminate edge conditions during insertions and removals
        self._head = Node()  # MRU sentinel
        self._tail = Node()  # LRU sentinel
        self._head.next = self._tail
        self._tail.prev = self._head

    # --------------------------------------------------------------------------
    # Internal Doubly Linked List Operations (O(1))
    # --------------------------------------------------------------------------

    def _add_node(self, node: Node) -> None:
        """Add node immediately after sentinel head (Most Recently Used position)."""
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node

    def _remove_node(self, node: Node) -> None:
        """Unlink node from its current position in the Doubly Linked List."""
        prev_node = node.prev
        next_node = node.next
        if prev_node:
            prev_node.next = next_node
        if next_node:
            next_node.prev = prev_node
        node.prev = None
        node.next = None

    def _move_to_head(self, node: Node) -> None:
        """Move an existing node to the MRU position (head)."""
        self._remove_node(node)
        self._add_node(node)

    def _pop_tail(self) -> Node:
        """Remove and return the Least Recently Used node (right before sentinel tail)."""
        lru_node = self._tail.prev
        if lru_node is self._head or lru_node is None:
            raise IndexError("Cannot pop from an empty cache")
        self._remove_node(lru_node)
        return lru_node

    # --------------------------------------------------------------------------
    # Public Cache Interface
    # --------------------------------------------------------------------------

    def get(self, key: Any) -> Any:
        """
        Retrieve value by key.
        
        Returns:
            The stored value if the key exists and has not expired; otherwise -1.
            A successful get() promotes the key to the Most Recently Used position.
            
        Time Complexity: O(1) average.
        """
        lock = self._lock
        if lock:
            with lock:
                return self._get_unlocked(key)
        return self._get_unlocked(key)

    def _get_unlocked(self, key: Any) -> Any:
        if key not in self._map:
            return -1

        node = self._map[key]

        # Check for TTL expiration
        if node.is_expired():
            # Lazy expiration: remove expired node immediately
            self._remove_node(node)
            del self._map[key]
            return -1

        # Move to head as Most Recently Used
        self._move_to_head(node)
        return node.value

    def put(
        self,
        key: Any,
        value: Any,
        ttl: Optional[float] = None,
    ) -> Optional[tuple[Any, Any]]:
        """
        Insert or update a key-value pair, with optional TTL in seconds.
        
        If the cache exceeds capacity, evicts the Least Recently Used (LRU) entry.
        
        Returns:
            A tuple of (evicted_key, evicted_value) if an eviction occurred, else None.
            
        Time Complexity: O(1) average.
        """
        lock = self._lock
        if lock:
            with lock:
                return self._put_unlocked(key, value, ttl)
        return self._put_unlocked(key, value, ttl)

    def _put_unlocked(
        self,
        key: Any,
        value: Any,
        ttl: Optional[float] = None,
    ) -> Optional[tuple[Any, Any]]:
        expires_at = (time.time() + ttl) if (ttl is not None and ttl > 0) else None
        evicted = None

        if key in self._map:
            # Update existing entry
            node = self._map[key]
            node.value = value
            node.expires_at = expires_at
            self._move_to_head(node)
        else:
            # Check capacity before insertion
            if len(self._map) >= self.capacity:
                lru_node = self._pop_tail()
                del self._map[lru_node.key]
                evicted = (lru_node.key, lru_node.value)

            new_node = Node(key=key, value=value, expires_at=expires_at)
            self._map[key] = new_node
            self._add_node(new_node)

        return evicted

    def peek(self, key: Any) -> Any:
        """
        Inspect a value by key without updating its LRU ordering.
        Returns -1 if not found or expired.
        """
        lock = self._lock
        if lock:
            with lock:
                return self._peek_unlocked(key)
        return self._peek_unlocked(key)

    def _peek_unlocked(self, key: Any) -> Any:
        if key not in self._map:
            return -1
        node = self._map[key]
        if node.is_expired():
            self._remove_node(node)
            del self._map[key]
            return -1
        return node.value

    def delete(self, key: Any) -> bool:
        """Explicitly remove a key from cache. Returns True if removed, False if not found."""
        lock = self._lock
        if lock:
            with lock:
                return self._delete_unlocked(key)
        return self._delete_unlocked(key)

    def _delete_unlocked(self, key: Any) -> bool:
        if key not in self._map:
            return False
        node = self._map.pop(key)
        self._remove_node(node)
        return True

    def clear(self) -> None:
        """Reset the cache to an empty state."""
        lock = self._lock
        if lock:
            with lock:
                self._clear_unlocked()
        else:
            self._clear_unlocked()

    def _clear_unlocked(self) -> None:
        self._map.clear()
        self._head.next = self._tail
        self._tail.prev = self._head

    def items(self) -> list[tuple[Any, Any]]:
        """Return list of (key, value) pairs from Most Recently Used (MRU) to Least Recently Used (LRU)."""
        lock = self._lock
        if lock:
            with lock:
                return self._items_unlocked()
        return self._items_unlocked()

    def _items_unlocked(self) -> list[tuple[Any, Any]]:
        result = []
        curr = self._head.next
        now = time.time()
        while curr is not self._tail and curr is not None:
            if not curr.is_expired(now):
                result.append((curr.key, curr.value))
            curr = curr.next
        return result

    def keys(self) -> list[Any]:
        """Return list of keys from MRU to LRU."""
        return [k for k, _ in self.items()]

    def values(self) -> list[Any]:
        """Return list of values from MRU to LRU."""
        return [v for _, v in self.items()]

    def state_display(self) -> str:
        """Return an ASCII representation of the internal DLL state."""
        items = self.items()
        if not items:
            return "[Empty Cache]"
        parts = [f"({k}: {v})" for k, v in items]
        return "MRU [ " + " <-> ".join(parts) + " ] LRU"

    def __len__(self) -> int:
        lock = self._lock
        if lock:
            with lock:
                return len(self.items())
        return len(self.items())

    def __contains__(self, key: Any) -> bool:
        return self.peek(key) != -1

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(capacity={self.capacity}, items={self.items()})"


# Direct alias matching problem statement signature: Cache(capacity)
Cache = LRUCache


class TTLCache(LRUCache):
    """
    LRU Cache with integrated Time-To-Live (TTL) support.
    
    Provides both:
    1. Passive/Lazy expiration on get() and peek()
    2. Active/Proactive cleanup via cleanup_expired()
    """

    def __init__(
        self,
        capacity: int,
        default_ttl: Optional[float] = None,
        thread_safe: bool = True,
    ) -> None:
        super().__init__(capacity=capacity, thread_safe=thread_safe)
        if default_ttl is not None and default_ttl <= 0:
            raise ValueError(f"Default TTL must be positive, got {default_ttl}")
        self.default_ttl = default_ttl

    def put(
        self,
        key: Any,
        value: Any,
        ttl: Optional[float] = None,
    ) -> Optional[tuple[Any, Any]]:
        effective_ttl = ttl if ttl is not None else self.default_ttl
        return super().put(key, value, ttl=effective_ttl)

    def get_remaining_ttl(self, key: Any) -> Optional[float]:
        """
        Get remaining time in seconds before key expires.
        Returns:
            - float > 0: remaining seconds
            - None: key exists with no expiration
            - -1: key not found or already expired
        """
        lock = self._lock
        if lock:
            with lock:
                return self._get_remaining_ttl_unlocked(key)
        return self._get_remaining_ttl_unlocked(key)

    def _get_remaining_ttl_unlocked(self, key: Any) -> Optional[float]:
        if key not in self._map:
            return -1
        node = self._map[key]
        if node.is_expired():
            self._remove_node(node)
            del self._map[key]
            return -1
        if node.expires_at is None:
            return None
        return max(0.0, node.expires_at - time.time())

    def cleanup_expired(self) -> int:
        """
        Actively sweep and remove all expired keys from the cache.
        Returns the count of evicted expired keys.
        """
        lock = self._lock
        if lock:
            with lock:
                return self._cleanup_expired_unlocked()
        return self._cleanup_expired_unlocked()

    def _cleanup_expired_unlocked(self) -> int:
        now = time.time()
        expired_keys = []
        curr = self._head.next
        while curr is not self._tail and curr is not None:
            if curr.is_expired(now):
                expired_keys.append(curr.key)
            curr = curr.next

        for key in expired_keys:
            node = self._map.pop(key)
            self._remove_node(node)

        return len(expired_keys)
