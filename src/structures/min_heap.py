"""Binary min-heap priority queue implementation."""

from typing import Generic, TypeVar

T = TypeVar("T")


class MinHeap(Generic[T]):
    """Array-backed binary min-heap with O(log n) push and pop operations."""

    def __init__(self) -> None:
        self._heap: list[tuple[float, int, T]] = []
        self._counter: int = 0

    def push(self, priority: float, item: T) -> None:
        """Insert an item with the given priority in O(log n) time."""
        self._heap.append((priority, self._counter, item))
        self._counter += 1
        self._sift_up(len(self._heap) - 1)

    def pop(self) -> tuple[float, T]:
        """Remove and return the (priority, item) with minimum priority in O(log n) time."""
        if not self._heap:
            raise IndexError("Cannot pop from an empty MinHeap.")

        top_priority, _, top_item = self._heap[0]
        last_entry = self._heap.pop()

        if self._heap:
            self._heap[0] = last_entry
            self._sift_down(0)

        return top_priority, top_item

    def peek(self) -> tuple[float, T]:
        """Return the minimum (priority, item) without removing it in O(1) time."""
        if not self._heap:
            raise IndexError("Cannot peek into an empty MinHeap.")

        top_priority, _, top_item = self._heap[0]
        return top_priority, top_item

    def is_empty(self) -> bool:
        """Return True if the heap contains no items."""
        return len(self._heap) == 0

    def _is_smaller(self, idx_a: int, idx_b: int) -> bool:
        entry_a = self._heap[idx_a]
        entry_b = self._heap[idx_b]
        return (entry_a[0], entry_a[1]) < (entry_b[0], entry_b[1])

    def _sift_up(self, index: int) -> None:
        while index > 0:
            parent = (index - 1) // 2
            if self._is_smaller(index, parent):
                self._heap[index], self._heap[parent] = (
                    self._heap[parent],
                    self._heap[index],
                )
                index = parent
            else:
                break

    def _sift_down(self, index: int) -> None:
        size = len(self._heap)
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2

            if left < size and self._is_smaller(left, smallest):
                smallest = left
            if right < size and self._is_smaller(right, smallest):
                smallest = right

            if smallest != index:
                self._heap[index], self._heap[smallest] = (
                    self._heap[smallest],
                    self._heap[index],
                )
                index = smallest
            else:
                break

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return len(self._heap) > 0
