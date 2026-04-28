# Sieve of Eratosthenes

## 1. TL;DR

The Sieve of Eratosthenes generates all primes up to N by iteratively marking the multiples of each prime as composite, starting at p². The signal is "primes up to N," "count primes," prime factorization queries, or any problem where you need a batch of primes or many factorizations with N up to ~10⁷. Time: O(N log log N) classical; O(N) linear sieve. Space: O(N).

## 2. Intuition

Every composite number has at least one prime factor ≤ its square root. So for each prime p found so far, all composites `k*p` with `k < p` have already been marked by a smaller prime. Starting the inner loop at p² avoids redundant work. The total number of marking operations is `Σ N/p over primes p ≤ N`, which by Mertens' theorem converges to O(N log log N) — nearly linear in practice.

The **smallest-prime-factor (SPF) table** variant builds a table `spf[i]` = smallest prime dividing `i`. Once built, factorizing any `n ≤ N` takes O(log n): repeatedly divide `n` by `spf[n]` until `n == 1`. This is the engine behind fast batch factorization.

## 3. Walkthrough

Sieve up to 30. Initialize `is_prime[0..30]` all `True`, then set `is_prime[0] = is_prime[1] = False`.

**p = 2:** mark 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30.
**p = 3:** start at 3² = 9; mark 9, 15, 21, 27 (6, 12, 18, 24 already marked).
**p = 4:** composite, skip.
**p = 5:** start at 5² = 25; mark 25, 30 already done → only 25 is new.
**p = 6 and beyond:** skip composites; once p > √30 ≈ 5.47, all remaining `True` entries are prime.

Remaining `True` positions: **[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]**.

```
index:  0  1  2  3  4  5  6  7  8  9 10 11 12 ...
prime:  F  F  T  T  F  T  F  T  F  F  F  T  F ...
```

## 4. Implementation

```python
from __future__ import annotations
import math


def sieve(n: int) -> list[int]:
    """Return all primes <= n using the classical Sieve of Eratosthenes."""
    if n < 2:
        return []
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for p in range(2, math.isqrt(n) + 1):
        if is_prime[p]:
            # start at p*p; smaller multiples already marked by smaller primes
            for multiple in range(p * p, n + 1, p):
                is_prime[multiple] = False
    return [i for i, flag in enumerate(is_prime) if flag]


def smallest_prime_factor(n: int) -> list[int]:
    """Return SPF table of length n+1.

    spf[i] = smallest prime factor of i, for i >= 2.
    spf[0] = spf[1] = 0 (sentinel; 0 and 1 have no prime factors).
    Factorize any k <= n in O(log k): divide by spf[k] repeatedly.
    """
    if n < 2:
        return [0] * (n + 1)
    spf = list(range(n + 1))  # spf[i] = i initially (optimistic: i is its own SPF)
    spf[0] = spf[1] = 0       # sentinel
    for p in range(2, math.isqrt(n) + 1):
        if spf[p] == p:        # p is prime (its SPF hasn't been updated)
            for multiple in range(p * p, n + 1, p):
                if spf[multiple] == multiple:  # not yet assigned a smaller factor
                    spf[multiple] = p
    return spf


def factorize(n: int, spf: list[int]) -> dict[int, int]:
    """Return prime factorization of n using a precomputed SPF table.

    Returns {prime: exponent, ...}. O(log n) per call.
    Requires n >= 2 and len(spf) > n.
    """
    factors: dict[int, int] = {}
    while n > 1:
        p = spf[n]
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
    return factors


if __name__ == "__main__":
    # Smoke tests
    result = sieve(30)
    assert result == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29], f"got {result}"

    spf = smallest_prime_factor(30)
    assert spf[2] == 2
    assert spf[4] == 2    # 4 = 2*2
    assert spf[15] == 3   # 15 = 3*5
    assert spf[0] == 0
    assert spf[1] == 0

    assert factorize(12, spf) == {2: 2, 3: 1}   # 12 = 2^2 * 3
    assert factorize(30, spf) == {2: 1, 3: 1, 5: 1}

    print("All smoke tests passed.")
```

**Template:**

```python
import math


def sieve(n: int) -> list[int]:
    if n < 2:
        return []
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for p in range(2, math.isqrt(n) + 1):
        if is_prime[p]:
            for multiple in range(p * p, n + 1, p):
                is_prime[multiple] = False
    return [i for i, flag in enumerate(is_prime) if flag]


def smallest_prime_factor(n: int) -> list[int]:
    if n < 2:
        return [0] * (n + 1)
    spf = list(range(n + 1))
    spf[0] = spf[1] = 0
    for p in range(2, math.isqrt(n) + 1):
        if spf[p] == p:
            for multiple in range(p * p, n + 1, p):
                if spf[multiple] == multiple:
                    spf[multiple] = p
    return spf


def factorize(n: int, spf: list[int]) -> dict[int, int]:
    factors: dict[int, int] = {}
    while n > 1:
        p = spf[n]
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
    return factors
```

## 5. Variants & pitfalls

### Variants

- **Classical sieve** (this file): boolean `is_prime` array, O(N log log N).
- **SPF (smallest prime factor) table**: initialize `spf[i] = i`; for each prime p, mark multiples starting at p² if they haven't been assigned a smaller factor yet. Gives O(log n) factorization queries.
- **Linear sieve (O(N))**: each composite is marked exactly once by its smallest prime factor. Slightly more complex: maintain a list of found primes and for each i, iterate primes p ≤ spf[i], marking i*p with spf[i*p] = p, stopping when p == spf[i]. Avoids redundant marking.
- **Segmented sieve**: for large ranges [L, R] (e.g., R up to 10¹²). Sieve primes up to √R using the classical sieve, then use those primes to mark composites in a shifted array of size R-L+1. Memory stays O(√R + (R-L)).

### Pitfalls

- **Starting inner loop at `2*p` instead of `p²`**: correct, but misses the O(N log log N) optimization (redundant marking of smaller multiples). The optimization matters for large N.
- **Array length off-by-one**: use `[True] * (n + 1)` to include index n; a common mistake is `[True] * n` which excludes n itself.
- **Using the sieve for very large N (N > ~10⁷–10⁸)**: memory blows up (100 MB for N=10⁸ with booleans). For primality testing of a single large number, use the **Miller-Rabin probabilistic primality test** instead.
- **SPF table sentinel**: `spf[0]` and `spf[1]` must be 0 (or otherwise marked invalid) since 0 and 1 are not prime. Failing to handle them causes infinite loops in `factorize`.
- **Calling `factorize(1, spf)`**: the while-loop exits immediately (correct), returning `{}`.

## 6. Complexity

- **Time:** O(N log log N) classical sieve — the harmonic series over reciprocals of primes up to N converges to log log N by Mertens' second theorem. O(N) for the linear sieve variant.
- **Space:** O(N) — the boolean (or SPF) array of length N+1 dominates.

## 7. Problem set

- [Medium] [Count Primes](https://leetcode.com/problems/count-primes/) — direct application: `len(sieve(n - 1))`.
- [Medium] [Prime Arrangements](https://leetcode.com/problems/prime-arrangements/) — count primes up to n, then multiply factorials modulo 10⁹+7.
- [Medium] [Closest Prime Numbers in Range](https://leetcode.com/problems/closest-prime-numbers-in-range/) — sieve the range, then scan for consecutive primes with the smallest gap.
- [Hard] [Largest Component Size by Common Factor](https://leetcode.com/problems/largest-component-size-by-common-factor/) — factorize each number (SPF table or trial division), union each number with its prime factors using Union-Find.
- [Hard] [Distinct Prime Factors of Product of Array](https://leetcode.com/problems/distinct-prime-factors-of-product-of-array/) — SPF factorize each element, collect all distinct primes in a set.
- [Hard] [Prime Subtraction Operation](https://leetcode.com/problems/prime-subtraction-operation/) — precompute primes up to 1000 with the sieve, then binary-search for the right prime to subtract at each step.

## 8. Related patterns

- [GCD](gcd.md) — GCD and factorization share the same number-theory setting; LC 952 uses factorization + Union-Find.
- [Union-Find](../graphs/union-find.md) — LC 952 (Largest Component Size by Common Factor) combines SPF factorization with DSU: union each number to its prime factors and find the largest component.
- **[Fast Exponentiation](fast-exponentiation.md)** — modular exponentiation underlies Miller-Rabin primality testing and `pow(a, p-2, p)` for modular inverses with prime moduli.

## 9. Interviewer follow-ups

**Q: How would you test primality for a single very large number (e.g., 2⁶⁴)?**
Use the **Miller-Rabin probabilistic primality test**. It runs in O(k log² n) where k is the number of witness rounds (typically 5–20 for a negligible error probability). A deterministic variant with a fixed set of witnesses (e.g., {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37}) is proven correct for all n < 3.3 × 10²⁴. Python's built-in `sympy.isprime` uses this.

**Q: How would you factorize many numbers up to 10⁶ quickly?**
Build a smallest-prime-factor (SPF) table once in O(N log log N) time and O(N) space. Then each factorization query runs in O(log n): repeatedly divide `n` by `spf[n]` until `n == 1`. This handles 10⁶ queries on numbers up to 10⁶ in well under a second.

**Q: What if you need primes in a huge range [L, R] where R is up to 10¹²?**
Use the **segmented sieve**: first sieve all primes up to √R (at most ~10⁶ primes), then use those as "stencils" to mark composites in a sliding window of size R-L+1. Memory stays O(√R + window_size) rather than O(R).

---

## RECALL

Sieve of Eratosthenes: mark composites by walking multiples of each prime p starting at p². Total work ≈ O(N log log N). SPF table gives O(log n) factorization: `spf[i]` = smallest prime dividing `i`; divide by `spf[n]` repeatedly. Signal: "primes up to N," "count primes," batch factorizations. Pitfalls: array must be length N+1; start inner loop at p², not 2p; for single huge numbers use Miller-Rabin instead.

```python
import math


def sieve(n: int) -> list[int]:
    if n < 2:
        return []
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for p in range(2, math.isqrt(n) + 1):
        if is_prime[p]:
            for multiple in range(p * p, n + 1, p):
                is_prime[multiple] = False
    return [i for i, flag in enumerate(is_prime) if flag]


def smallest_prime_factor(n: int) -> list[int]:
    if n < 2:
        return [0] * (n + 1)
    spf = list(range(n + 1))
    spf[0] = spf[1] = 0
    for p in range(2, math.isqrt(n) + 1):
        if spf[p] == p:
            for multiple in range(p * p, n + 1, p):
                if spf[multiple] == multiple:
                    spf[multiple] = p
    return spf


def factorize(n: int, spf: list[int]) -> dict[int, int]:
    factors: dict[int, int] = {}
    while n > 1:
        p = spf[n]
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
    return factors
```
