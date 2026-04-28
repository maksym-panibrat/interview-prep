# Reservoir Sampling

## 1. TL;DR

Reservoir sampling gives you a **uniformly random sample of k items from a stream of unknown size** without storing the whole stream. The signal is "pick k random elements from a stream," "data doesn't fit in memory," or "uniform random sample without knowing n in advance." For k=1: keep the first element; on the i-th element replace with probability `1/i`. For general k: fill the reservoir with the first k elements; on the i-th element (i > k) replace a random reservoir slot with probability `k/i`. Time: O(n). Space: O(k).

## 2. Intuition

Imagine you're assigned a seat on an arriving train of unknown length. As each new car arrives you toss a coin weighted toward giving the newcomer a fair chance. After the train stops, every passenger has had exactly equal odds — no matter how long the ride.

For k=1: when the i-th element arrives you want each of the i elements seen so far to have equal probability `1/i` of being the current holder. The recurrence is: keep the current holder with probability `(i-1)/i` and swap in the newcomer with probability `1/i`. By induction, every element seen so far has probability exactly `1/i` after processing element i.

For k>1: fill the first k slots directly. For the i-th element (i > k) the new item should end up in the reservoir with probability `k/i`. Accept it with that probability, then randomly evict one of the k current residents — preserving the uniform invariant for all k slots.

The algorithm is **online**: it processes each element exactly once, maintains a fixed-size reservoir, and never looks backward.

## 3. Walkthrough

### k=1 on stream `[A, B, C, D]`

```
i=1  A arrives: reservoir = [A].                           P(A chosen) = 1.
i=2  B arrives: replace with prob 1/2.
     P(A survives) = 1 * (1 - 1/2) = 1/2
     P(B chosen)  = 1/2
i=3  C arrives: replace with prob 1/3.
     P(A survives to here) = 1/2 * (2/3) = 1/3
     P(B survives to here) = 1/2 * (2/3) = 1/3
     P(C chosen)           = 1/3
i=4  D arrives: replace with prob 1/4.
     P(A survives) = 1/3 * (3/4) = 1/4
     P(B survives) = 1/3 * (3/4) = 1/4
     P(C survives) = 1/3 * (3/4) = 1/4
     P(D chosen)  = 1/4  all equal
```

### k=2 on stream `[A, B, C, D, E]`

```
i=1,2  Fill reservoir: [A, B].
i=3  C: accept with prob 2/3; if accepted, evict A or B (50/50).
i=4  D: accept with prob 2/4 = 1/2; if accepted, evict a random slot.
i=5  E: accept with prob 2/5; if accepted, evict a random slot.
```

After all 5 elements each of the C(5,2)=10 pairs is equally likely. Each element has probability 2/5 of appearing in the final reservoir.

## 4. Implementation

```python
from __future__ import annotations

import random
from typing import Iterator, List, TypeVar

T = TypeVar("T")


def reservoir_sample_one(stream: Iterator[T]) -> T:
    """Uniformly sample a single item from a stream of unknown length.

    Uses Algorithm R (Vitter 1985) for k=1.
    Raises StopIteration if the stream is empty.
    """
    reservoir = next(stream)  # guaranteed first element; raises if empty
    for i, item in enumerate(stream, start=2):
        # replace current reservoir with probability 1/i
        if random.randrange(i) == 0:
            reservoir = item
    return reservoir


def reservoir_sample_k(stream: Iterator[T], k: int) -> List[T]:
    """Uniformly sample k items from a stream of unknown length.

    Uses Algorithm R (Vitter 1985).
    Returns fewer than k items only if the stream has fewer than k elements.
    """
    reservoir: List[T] = []
    for i, item in enumerate(stream, start=1):
        if len(reservoir) < k:
            reservoir.append(item)
        else:
            # replace a random slot with probability k/i
            j = random.randrange(i)
            if j < k:
                reservoir[j] = item
    return reservoir


if __name__ == "__main__":
    import collections

    # Smoke test: sample_one over 1000 trials — each of 4 items should appear ~25%
    random.seed(42)
    population = ["A", "B", "C", "D"]
    trials = 1000
    counts: dict = collections.Counter(
        reservoir_sample_one(iter(population)) for _ in range(trials)
    )
    expected = trials / len(population)
    tolerance = 0.10  # allow +-10% of expected
    for val in population:
        freq = counts[val] / trials
        assert abs(freq - 1 / len(population)) < tolerance, (
            f"{val}: freq={freq:.3f}, expected approx {1/len(population):.3f}"
        )
    print("Smoke test passed:", dict(counts))

    # Basic correctness checks
    assert reservoir_sample_one(iter([42])) == 42
    assert set(reservoir_sample_k(iter(range(10)), 3)).issubset(set(range(10)))
    assert len(reservoir_sample_k(iter(range(5)), 10)) == 5  # fewer than k items
    print("All smoke tests passed.")
```

**Template:**

```python
import random
from typing import Iterator, List, TypeVar

T = TypeVar("T")


def reservoir_sample_one(stream: Iterator[T]) -> T:
    reservoir = next(stream)
    for i, item in enumerate(stream, start=2):
        if random.randrange(i) == 0:
            reservoir = item
    return reservoir


def reservoir_sample_k(stream: Iterator[T], k: int) -> List[T]:
    reservoir: List[T] = []
    for i, item in enumerate(stream, start=1):
        if len(reservoir) < k:
            reservoir.append(item)
        else:
            j = random.randrange(i)
            if j < k:
                reservoir[j] = item
    return reservoir
```

## 5. Variants & pitfalls

### Algorithm A-Res (weighted reservoir sampling)

When items carry weights, assign each item a key `r^(1/w)` where `r` is uniform in `(0, 1]` and `w` is the item weight. Maintain a min-heap of size k keyed by these values; replace the minimum-key item whenever a new item's key exceeds the heap minimum. Items with larger weights get larger keys on average, so they are proportionally more likely to survive.

### Distributed / sharded reservoirs

Each shard independently runs Algorithm R to produce a local reservoir of size k. Merging shards: treat each shard's reservoir as a weighted stream where each item represents `n_shard / k` original items. In practice you can merge two reservoirs of size k by simulating Algorithm R treating both as a single stream of 2k candidates.

### Pitfalls

- **Off-by-one**: the i index must start at 1 (not 0). Using `random.randrange(i) == 0` requires i >= 1; the first element is accepted unconditionally (probability 1/1 = 1).
- **Non-uniform RNG**: using `random.random() < 1/i` with floating-point division introduces tiny bias for very large i; `random.randrange(i) == 0` is exact.
- **Assuming n is known**: the whole point is you do *not* know n in advance. If you find yourself pre-computing stream length, you don't need reservoir sampling.
- **Replacing a fixed slot for k>1**: always pick a *random* slot `j = random.randrange(i); if j < k: reservoir[j] = item`. Replacing slot 0 every time concentrates all replacement probability on one slot, destroying uniformity.

## 6. Complexity

- **Time:** O(n) — each of the n stream elements is processed exactly once with O(1) work per element.
- **Space:** O(k) — only the k-element reservoir is kept in memory regardless of stream length.

## 7. Problem set

- [Medium] [Linked List Random Node](https://leetcode.com/problems/linked-list-random-node/) — direct k=1 application on a linked list; tests that you implement the online algorithm correctly.
- [Medium] [Random Pick Index](https://leetcode.com/problems/random-pick-index/) — reservoir sampling for a specific target value; illustrates that you can sample from a filtered sub-stream inline.
- [Medium] [Insert Delete GetRandom O(1) - Duplicates allowed](https://leetcode.com/problems/insert-delete-getrandom-o1-duplicates-allowed/) — different mechanism (index-swap with hash map) for uniform random pick from a mutable set; contrasts with reservoir sampling.

## 8. Related patterns

- [Sliding Window](../two-pointers-sliding-window/sliding-window.md) — another streaming pattern that maintains a fixed-size window over a stream; differs in that sliding window processes a contiguous subarray rather than a random subset.

## 9. Interviewer follow-ups

**Q: Prove correctness for k=1.**
Induction on stream length n. Base case n=1: the single element is chosen with probability 1 = 1/1. Inductive step: assume after seeing i elements each has probability 1/i of being in the reservoir. When element i+1 arrives it is chosen with probability 1/(i+1). The current holder survives with probability 1 - 1/(i+1) = i/(i+1). So each of the previous i holders now has probability (1/i) * (i/(i+1)) = 1/(i+1). Combined with the new element: all i+1 elements have probability 1/(i+1). QED.

**Q: Weighted version?**
Use Algorithm A-Res. Each item with weight `w_i` gets a priority key `k_i = r_i^(1/w_i)` where `r_i` is drawn uniformly from `(0, 1]`. Maintain a min-heap of size k over these keys. For each new item compute its key; if it exceeds the heap minimum, pop the minimum and push the new item. Items with larger weights produce larger keys on average, making them proportionally more likely to survive in the reservoir.
