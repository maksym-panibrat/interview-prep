# GCD

## 1. TL;DR

GCD (Greatest Common Divisor) computes the largest integer that divides both `a` and `b` using the Euclidean recurrence `gcd(a, b) = gcd(b, a mod b)`. The signal is "common factor," "fraction in lowest terms," "LCM," "lattice problems on integers," or "modular inverse via extended Euclidean." Extended Euclidean additionally returns Bézout coefficients `x, y` satisfying `a*x + b*y = gcd(a, b)` — the basis for modular inverses. Time: O(log(min(a, b))). Space: O(1) iterative.

## 2. Intuition

Every common divisor of `a` and `b` also divides `a mod b` (because `a mod b = a - b * floor(a/b)`, so any factor of both `a` and `b` must also divide the remainder). This means `gcd(a, b) = gcd(b, a mod b)`. The remainder strictly decreases at each step, so the sequence terminates. In the worst case the inputs are consecutive Fibonacci numbers — even then the recursion depth is O(log(min(a, b))).

Extended Euclidean works the same way but additionally tracks how each remainder can be expressed as a linear combination of the original `a` and `b`. Starting from `gcd(g, 0) = g = g*1 + 0*0`, coefficients propagate back up the recursion via `x_prev = y_curr` and `y_prev = x_curr - q * y_curr`. The resulting `(g, x, y)` satisfies `a*x + b*y = g` — Bézout's identity.

For modular inverses: `a^{-1} mod m` exists iff `gcd(a, m) = 1`. Extended Euclidean gives `a*x + m*y = 1`, so `a*x ≡ 1 (mod m)`, meaning `x mod m` is the inverse. For a prime modulus `p`, Fermat's little theorem gives the shortcut `pow(a, p-2, p)`.

## 3. Walkthrough

### Classical GCD: `gcd(48, 18)`

| step | a  | b  | a mod b |
|------|----|----|---------|
| 1    | 48 | 18 | 12      |
| 2    | 18 | 12 | 6       |
| 3    | 12 | 6  | 0       |
| 4    | 6  | 0  | —       |

`b == 0`, return `a = 6`.

### Extended GCD: `extgcd(48, 18)`

We track `(g, x, y)` at each recursive level:

```
extgcd(48, 18) calls extgcd(18, 12)
  extgcd(18, 12) calls extgcd(12, 6)
    extgcd(12, 6) calls extgcd(6, 0)
      base case: return (6, 1, 0)        => 6*1 + 0*0 = 6
    q = 12 // 6 = 2
    x = 0, y = 1 - 2*0 = 1
    return (6, 0, 1)                     => 12*0 + 6*1 = 6
  q = 18 // 12 = 1
  x = 1, y = 0 - 1*1 = -1
  return (6, 1, -1)                      => 18*1 + 12*(-1) = 6
q = 48 // 18 = 2
x = -1, y = 1 - 2*(-1) = 3
return (6, -1, 3)                        => 48*(-1) + 18*3 = -48+54 = 6
```

Final result: `g=6, x=-1, y=3`. Check: `48*(-1) + 18*3 = -48 + 54 = 6`. Correct.

## 4. Implementation

```python
from __future__ import annotations
from functools import reduce
from typing import Optional


def gcd(a: int, b: int) -> int:
    """Iterative Euclidean GCD. Works for negative inputs (strips sign)."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a  # gcd(0, 0) == 0 by convention


def lcm(a: int, b: int) -> int:
    """LCM via gcd. Avoids intermediate overflow in other languages."""
    if a == 0 or b == 0:
        return 0
    return abs(a) // gcd(a, b) * abs(b)  # divide first to keep numbers small


def extgcd(a: int, b: int) -> tuple[int, int, int]:
    """Extended Euclidean algorithm.

    Returns (g, x, y) such that a*x + b*y == g == gcd(a, b).
    Works for non-negative a, b. If b == 0 the base case returns directly.
    """
    if b == 0:
        return a, 1, 0  # a*1 + 0*0 = a
    g, x1, y1 = extgcd(b, a % b)
    # extgcd(b, a%b) gave b*x1 + (a%b)*y1 = g
    # substitute a%b = a - q*b:
    # b*x1 + (a - q*b)*y1 = g  =>  a*y1 + b*(x1 - q*y1) = g
    q = a // b
    return g, y1, x1 - q * y1


def modinv(a: int, m: int) -> Optional[int]:
    """Modular inverse of a mod m via extended Euclidean.

    Returns x such that a*x == 1 (mod m), or None if gcd(a, m) != 1.
    """
    g, x, _ = extgcd(a % m, m)
    if g != 1:
        return None  # inverse does not exist
    return x % m


if __name__ == "__main__":
    # gcd smoke tests
    assert gcd(48, 18) == 6
    assert gcd(18, 48) == 6
    assert gcd(0, 5) == 5
    assert gcd(5, 0) == 5
    assert gcd(0, 0) == 0
    assert gcd(-12, 8) == 4

    # lcm smoke tests
    assert lcm(4, 6) == 12
    assert lcm(0, 5) == 0
    assert lcm(7, 1) == 7

    # extgcd smoke test: 48*x + 18*y == 6
    g, x, y = extgcd(48, 18)
    assert g == 6
    assert 48 * x + 18 * y == 6, f"48*{x} + 18*{y} = {48*x + 18*y} != 6"

    # modinv smoke tests
    assert modinv(3, 7) == 5    # 3*5 = 15 == 1 (mod 7)
    assert modinv(7, 13) == 2   # 7*2 = 14 == 1 (mod 13)
    assert modinv(2, 4) is None  # gcd(2, 4) = 2 != 1

    # gcd of array via reduce
    arr = [12, 18, 24]
    assert reduce(gcd, arr) == 6

    print("All smoke tests passed.")
```

**Template:**

```python
from functools import reduce
from typing import Optional


def gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return abs(a) // gcd(a, b) * abs(b)


def extgcd(a: int, b: int) -> tuple[int, int, int]:
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extgcd(b, a % b)
    q = a // b
    return g, y1, x1 - q * y1


def modinv(a: int, m: int) -> Optional[int]:
    g, x, _ = extgcd(a % m, m)
    if g != 1:
        return None
    return x % m
```

## 5. Variants & pitfalls

### Classical Euclidean

The iterative `while b: a, b = b, a % b` is preferred over recursion in Python to avoid stack depth issues on very large inputs (though the depth is O(log min) so it is rarely a problem in practice). Python 3.9+ has `math.gcd` built in.

### Extended Euclidean

The recursive form is cleaner to derive; the iterative form (tracking two rows of coefficients) is available but harder to recall under pressure. Stick with the recursive version — recursion depth is bounded by O(log min(a, b)).

### LCM via GCD

`lcm(a, b) = a * b // gcd(a, b)`. In Python there is no overflow, but in C++/Java divide *before* multiplying: `(a / gcd(a, b)) * b`. In Python 3.9+ `math.lcm` is built in.

### GCD of an array

`from functools import reduce; reduce(gcd, arr)`. Works because GCD is associative and commutative.

### Modular inverse — prime vs general modulus

- **Prime modulus** `p`: `pow(a, p - 2, p)` via Fermat's little theorem. One-liner, built-in fast exponentiation.
- **General modulus** `m` with `gcd(a, m) == 1`: use `modinv` above. Returns None if the inverse does not exist.

### Pitfalls

- **Integer overflow in other languages**: `a * b` in the LCM formula overflows 32/64-bit integers for large inputs. Always `(a // gcd(a, b)) * b` in C++/Java.
- **`gcd(0, 0) = 0`**: Some implementations raise an error; the convention in Python's `math.gcd` is to return 0. Handle this if the problem can have all-zero inputs.
- **Negative inputs**: GCD is conventionally non-negative. Strip signs with `abs()` at the entry point.
- **Confusing GCD with LCM**: GCD divides both numbers (result is at most min(a, b)); LCM is divisible by both (result is at least max(a, b)). Quick sanity check: `gcd(4, 6) = 2` (small), `lcm(4, 6) = 12` (large).
- **Extended GCD with negative `a`**: The implementation above passes `a % m` into `extgcd` when computing `modinv`, which ensures non-negative arguments. For raw `extgcd` with negative inputs, results may have unexpected signs — always verify `a*x + b*y == g`.

## 6. Complexity

- **Time:** O(log(min(a, b))) — each step replaces `b` with `a mod b`, which is less than `b/2` whenever `a >= 2b`; the Fibonacci pair `(F(n+1), F(n))` is the worst case, requiring exactly n steps.
- **Space:** O(1) iterative GCD; O(log(min(a, b))) recursive Extended GCD (recursion stack depth equals number of steps).

## 7. Problem set

- [Easy] [Greatest Common Divisor of Strings](https://leetcode.com/problems/greatest-common-divisor-of-strings/) — checks whether `t` divides `s` by string repetition; `gcd` on lengths gives the answer.
- [Easy] [Fraction Addition and Subtraction](https://leetcode.com/problems/fraction-addition-and-subtraction/) — parse fractions, fold via LCM for common denominator, reduce each result with GCD.
- [Easy] [X of a Kind in a Deck of Cards](https://leetcode.com/problems/x-of-a-kind-in-a-deck-of-cards/) — GCD of all group sizes must be at least 2; `reduce(gcd, counts) >= 2`.
- [Medium] [Find Greatest Common Divisor of Array](https://leetcode.com/problems/find-greatest-common-divisor-of-array/) — GCD of min and max of array; warm-up problem.
- [Medium] [Smallest Integer Divisible by K](https://leetcode.com/problems/smallest-integer-divisible-by-k/) — modular arithmetic; GCD check gates whether a solution exists.
- [Medium] [Divisor Game](https://leetcode.com/problems/divisor-game/) — math observation; parity argument, GCD tangential.
- [Hard] [Largest Component Size by Common Factor](https://leetcode.com/problems/largest-component-size-by-common-factor/) — Union-Find + factoring: union each number with all its prime factors, then find largest component.

## 8. Related patterns

- [Union-Find](../graphs/union-find.md) — used together in LC 952 (Largest Component Size by Common Factor): factorize each number and union it with its prime factors using DSU.
- **[Sieve of Eratosthenes](sieve.md)** — factorization needed for LC 952 and other number-theory problems pairs naturally with GCD.
- **[Fast Exponentiation](fast-exponentiation.md)** — `pow(a, p-2, p)` is the Fermat-based modular inverse; fast exponentiation is the engine that makes it O(log p).

## 9. Interviewer follow-ups

**Q: Modular inverse of 7 mod 13?**
13 is prime, so Fermat applies: `pow(7, 11, 13) = 2`. Verify: `7 * 2 = 14 == 1 (mod 13)`. Alternatively, `extgcd(7, 13)` returns `(1, 2, -1)` — same answer. Both give 2.

**Q: Why does the Euclidean algorithm terminate?**
Each step replaces `(a, b)` with `(b, a mod b)`. The value `a mod b < b`, so the second argument strictly decreases on every step. Since it is a non-negative integer it must eventually reach 0, at which point the algorithm returns. The Fibonacci pair `(F(n+1), F(n))` is the adversarial worst case, requiring n steps, giving the O(log(min(a, b))) bound.

**Q: How do you compute GCD of more than two numbers?**
GCD is associative: `gcd(a, b, c) = gcd(gcd(a, b), c)`. Use `from functools import reduce; reduce(gcd, arr)`. This runs in O(n log V) where n is the array length and V is the maximum value.
