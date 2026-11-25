"""Hash map implementation using separate chaining and dynamic resizing."""

from typing import Any, Generic, Iterator, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class HashMap(Generic[K, V]):
    """Hash table providing O(1) average-case lookup, insertion, and deletion."""

    def __init__(
        self, initial_capacity: int = 8, max_load_factor: float = 0.75
    ) -> None:
        if initial_capacity < 4:
            raise ValueError("Initial capacity must be at least 4.")
        if not (0.1 < max_load_factor < 1.0):
            raise ValueError("Load factor must be between 0.1 and 1.0.")

        self._capacity: int = initial_capacity
        self._max_load_factor: float = max_load_factor
        self._buckets: list[list[tuple[K, V]]] = [[] for _ in range(self._capacity)]
        self._size: int = 0

    @property
    def load_factor(self) -> float:
        """Return the current ratio of stored entries to bucket capacity."""
        return self._size / self._capacity

    @property
    def capacity(self) -> int:
        """Return the current number of buckets."""
        return self._capacity

    def _hash(self, key: K) -> int:
        return hash(key) % self._capacity

    def _resize(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._buckets = [[] for _ in range(self._capacity)]
        self._size = 0

        for bucket in old_buckets:
            for key, value in bucket:
                self.put(key, value)

    def put(self, key: K, value: V) -> None:
        """Insert or update a key-value pair in O(1) average time."""
        index = self._hash(key)
        bucket = self._buckets[index]

        for i, (existing_key, _) in enumerate(bucket):
            if existing_key == key:
                bucket[i] = (key, value)
                return

        if (self._size + 1) / self._capacity > self._max_load_factor:
            self._resize(self._capacity * 2)
            index = self._hash(key)
            bucket = self._buckets[index]

        bucket.append((key, value))
        self._size += 1

    def get(self, key: K, default: Any = None) -> Any:
        """Return the value for key if present, otherwise default."""
        index = self._hash(key)
        for existing_key, value in self._buckets[index]:
            if existing_key == key:
                return value
        return default

    def remove(self, key: K) -> V:
        """Remove key and return its value; raise KeyError if missing."""
        index = self._hash(key)
        bucket = self._buckets[index]

        for i, (existing_key, value) in enumerate(bucket):
            if existing_key == key:
                bucket.pop(i)
                self._size -= 1
                return value

        raise KeyError(key)

    def keys(self) -> list[K]:
        """Return a list of all keys stored in the map."""
        return [key for bucket in self._buckets for key, _ in bucket]

    def values(self) -> list[V]:
        """Return a list of all values stored in the map."""
        return [value for bucket in self._buckets for _, value in bucket]

    def items(self) -> list[tuple[K, V]]:
        """Return a list of all (key, value) pairs stored in the map."""
        return [(key, value) for bucket in self._buckets for key, value in bucket]

    def __getitem__(self, key: K) -> V:
        index = self._hash(key)
        for existing_key, value in self._buckets[index]:
            if existing_key == key:
                return value
        raise KeyError(key)

    def __setitem__(self, key: K, value: V) -> None:
        self.put(key, value)

    def __delitem__(self, key: K) -> None:
        self.remove(key)

    def __contains__(self, key: object) -> bool:
        index = hash(key) % self._capacity
        return any(existing_key == key for existing_key, _ in self._buckets[index])

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[K]:
        for bucket in self._buckets:
            for key, _ in bucket:
                yield key
