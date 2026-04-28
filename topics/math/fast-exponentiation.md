# Fast Exponentiation

## 1. TL;DR

Fast exponentiation (binary exponentiation) computes `x^n` in O(log n) multiplications by halving the exponent at each step: `x^n = (x^(n/2))²` when n is even, `x · (x^((n-1)/2))²` when n is odd. The signal is `pow(x, n)` for huge n, "compute x^n mod m," linear-recurrence speedups via matrix exponentiation (Fibonacci in O(log n)), or any problem requiring modular powers. Time: O(log n) scalar; O(k³ log n) for k×k matrix.

## 2. Intuition

Think of n written in binary: `n = b_t·2^t + … + b_1·2 + b_0`. Then `x^n = x^(b_t·2^t) · … · x^(b_1·2) · x^b_0`. Each term is `x` squared t times, so we can build all powers-of-two of `x` with t squarings and multiply only the ones whose bit is set. This decomposes one large exponentiation into O(log n) squarings and O(log n) multiplications.

The same logic applies when the "multiplication" is matrix multiplication: replacing scalar `x` with a square matrix `M` and accumulating `M^n` gives an O(k³ log n) algorithm for k×k matrices. Any linear recurrence `f(n) = a·f(n-1) + b·f(n-2) + …` can be encoded as a companion matrix, and matrix exponentiation evaluates f(n) in O(log n) steps.

## 3. Walkthrough

### Scalar: `2^10`

Bit decomposition: `10 = 0b1010 = 2³ + 2¹`. Iterate bits low-to-high, maintaining `cur = x^(2^i)` and accumulating into `result`:

| i | bit of 10 | cur (= 2^(2^i)) | result |
|---|-----------|-----------------|--------|
| 0 | 0         | 2               | 1      |
| 1 | 1         | 4               | 4      |
| 2 | 0         | 16              | 4      |
| 3 | 1         | 256             | 1024   |

Result: `2^10 = 1024`.

### Modular: `pow(3, 13, 7)` — compute `3^13 mod 7`

`13 = 0b1101 = 2³ + 2² + 2⁰`. Powers of 3 mod 7:

| i | bit of 13 | cur (= 3^(2^i) mod 7) | result |
|---|-----------|----------------------|--------|
| 0 | 1         | 3                    | 3      |
| 1 | 0         | 2  (3²=9 mod 7)      | 3      |
| 2 | 1         | 4  (2²=4 mod 7)      | 12 mod 7 = 5 |
| 3 | 1         | 2  (4²=16 mod 7)     | 5·2 mod 7 = 3 |

Result: `3^13 mod 7 = 3`. Verify: `3^13 = 1594323`; `1594323 mod 7 = 3`. Correct.

## 4. Implementation

```python
from __future__ import annotations
from typing import Optional


def pow_int(x: int, n: int) -> int:
    """Fast integer exponentiation: x^n for non-negative integer n.

    Iterates over bits of n low-to-high; squares x at each step
    and multiplies result when the current bit is set.
    """
    if n < 0:
        raise ValueError("pow_int requires n >= 0; use reciprocal for negative n")
    result = 1
    cur = x          # cur tracks x^(2^i) at bit position i
    while n:
        if n & 1:    # current bit is set: fold cur into result
            result *= cur
        cur *= cur   # square for the next bit position
        n >>= 1      # advance to the next bit
    return result


def pow_mod(x: int, n: int, mod: int) -> int:
    """Modular fast exponentiation: x^n mod m for non-negative n.

    Re-implements Python's three-arg pow() for clarity.
    Takes modulus after every multiplication to bound intermediate values.
    """
    if n < 0:
        raise ValueError("pow_mod requires n >= 0")
    result = 1 % mod  # handles mod == 1 → result stays 0
    cur = x % mod
    while n:
        if n & 1:
            result = result * cur % mod
        cur = cur * cur % mod
        n >>= 1
    return result


def mat_mult(
    A: list[list[int]], B: list[list[int]], mod: Optional[int] = None
) -> list[list[int]]:
    """Multiply two square matrices A and B (both k×k).

    If mod is provided, every entry is taken modulo mod.
    """
    k = len(A)
    C = [[0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            s = sum(A[i][t] * B[t][j] for t in range(k))
            C[i][j] = s % mod if mod is not None else s
    return C


def mat_pow(
    M: list[list[int]], n: int, mod: Optional[int] = None
) -> list[list[int]]:
    """Fast matrix exponentiation: M^n using binary exponentiation.

    Returns the identity matrix for n == 0.
    For a k×k matrix: O(k³ log n) multiplications.
    """
    k = len(M)
    # Identity matrix
    result = [[int(i == j) for j in range(k)] for i in range(k)]
    cur = [row[:] for row in M]   # copy so we don't mutate the input
    while n:
        if n & 1:
            result = mat_mult(result, cur, mod)
        cur = mat_mult(cur, cur, mod)
        n >>= 1
    return result


if __name__ == "__main__":
    # pow_int smoke test
    assert pow_int(2, 10) == 1024, f"got {pow_int(2, 10)}"
    assert pow_int(3, 0) == 1
    assert pow_int(0, 0) == 1   # convention: 0^0 = 1

    # pow_mod smoke test
    assert pow_mod(3, 13, 7) == 3, f"got {pow_mod(3, 13, 7)}"
    assert pow_mod(2, 10, 1000) == 24

    # mat_pow smoke test — Fibonacci via [[1,1],[1,0]]^10
    # [[1,1],[1,0]]^n == [[F(n+1), F(n)], [F(n), F(n-1)]]
    fib_matrix = [[1, 1], [1, 0]]
    result = mat_pow(fib_matrix, 10)
    assert result == [[89, 55], [55, 34]], f"got {result}"
    # F(11)=89, F(10)=55, F(9)=34 ✓

    print("All smoke tests passed.")
```

**Template:**

```python
from typing import Optional


def pow_int(x: int, n: int) -> int:
    result, cur = 1, x
    while n:
        if n & 1:
            result *= cur
        cur *= cur
        n >>= 1
    return result


def pow_mod(x: int, n: int, mod: int) -> int:
    result, cur = 1 % mod, x % mod
    while n:
        if n & 1:
            result = result * cur % mod
        cur = cur * cur % mod
        n >>= 1
    return result


def mat_mult(A, B, mod=None):
    k = len(A)
    C = [[0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            s = sum(A[i][t] * B[t][j] for t in range(k))
            C[i][j] = s % mod if mod is not None else s
    return C


def mat_pow(M, n, mod=None):
    k = len(M)
    result = [[int(i == j) for j in range(k)] for i in range(k)]
    cur = [row[:] for row in M]
    while n:
        if n & 1:
            result = mat_mult(result, cur, mod)
        cur = mat_mult(cur, cur, mod)
        n >>= 1
    return result
```

## 5. Variants & pitfalls

### Variants

- **Integer pow `x^n`**: use `pow_int` above or Python's built-in `pow(x, n)`. Handles arbitrarily large integers natively in Python.
- **Modular pow `x^n mod m`**: Python's three-arg `pow(x, n, m)` already does this in O(log n) and is the fastest option in practice. Implement `pow_mod` for understanding or when the multiplication step is customized.
- **Matrix exponentiation**: replace scalar multiply with `mat_mult`. Any linear recurrence with constant coefficients can be expressed as a companion matrix; raising it to the n-th power gives the n-th term in O(k³ log n). Example: Fibonacci with `[[1,1],[1,0]]^n`.
- **Negative exponents**: for floats use `1/x` as the base; for modular arithmetic, use the modular inverse `modinv(x, mod)` and then `pow_mod(modinv(x, mod), -n, mod)` (or equivalently `pow(x, -n % (mod-1), mod)` when mod is prime by Fermat's little theorem).

### Pitfalls

- **Off-by-one in the bit loop**: the loop condition is `while n:` (exit when n reaches 0), not `while n > 0`. Both are equivalent but `while n:` is more idiomatic.
- **Forgetting to reduce modulo at each step**: in Python integers don't overflow, but in C++/Java intermediate products can overflow 64-bit integers; always `(result * cur) % mod` after each multiplication, not only at the end.
- **Mutating the input matrix**: `mat_pow` copies M on entry (`cur = [row[:] for row in M]`) to avoid altering the caller's matrix.
- **Matrix multiplication non-commutativity**: `mat_mult(result, cur)` and `mat_mult(cur, result)` differ in general. Always keep the order consistent with the direction of the recurrence.
- **`n == 0` edge case**: the loop body never executes; `result` stays the identity scalar (1) or identity matrix, which is correct by definition `x^0 = 1`, `M^0 = I`.
- **`mod == 1`**: `1 % 1 == 0`, so `result = 1 % mod = 0` is the correct initialization — every integer mod 1 is 0.

## 6. Complexity

- **Time:** O(log n) — the exponent n is halved at each iteration (right-shifted by one bit), so the loop runs exactly `floor(log₂ n) + 1` times; each iteration is O(1) for scalars, O(k³) for k×k matrices.
- **Space:** O(1) auxiliary for scalar exponentiation; O(k²) for matrix exponentiation (two k×k matrices held at a time).

## 7. Problem set

- [Medium] [Pow(x, n)](https://leetcode.com/problems/powx-n/) — direct implementation; handle negative n and the edge case `n = -2^31`.
- [Medium] [Super Pow](https://leetcode.com/problems/super-pow/) — exponent given as an array of digits; use `pow(x, e, mod)` digit-by-digit with `a^(10b+c) = (a^b)^10 * a^c`.
- [Medium] [Count Good Numbers](https://leetcode.com/problems/count-good-numbers/) — count even-position and odd-position choices separately; each is a modular exponentiation.
- [Hard] [Knight Dialer](https://leetcode.com/problems/knight-dialer/) — encode reachable-digit transitions as a matrix; `M^(n-1) · initial_state` gives counts for n hops via matrix exponentiation in O(log n).
- [Hard] [N-th Tribonacci Number](https://leetcode.com/problems/n-th-tribonacci-number/) — small n, so linear DP suffices; matrix exponentiation (`[[1,1,1],[1,0,0],[0,1,0]]^n`) demonstrates the technique for larger recurrences.

## 8. Related patterns

- [GCD](gcd.md) — `pow(a, p-2, p)` is the Fermat-based modular inverse when p is prime; `extgcd` gives the inverse for composite moduli; both live in the same number-theory toolkit.
- [Sieve of Eratosthenes](sieve.md) — Miller-Rabin primality testing internally calls modular exponentiation (`pow(a, d, n)`) as its witness check.
- [1D DP](../dp/1d-dp.md) — linear recurrences like Fibonacci are also solved by 1D DP in O(n); matrix exponentiation is the O(log n) upgrade when n is astronomically large.

## 9. Interviewer follow-ups

**Q: How do you compute the n-th Fibonacci number in O(log n)?**
Use matrix exponentiation: `[[1,1],[1,0]]^n` gives `[[F(n+1), F(n)], [F(n), F(n-1)]]`. Raise the 2×2 companion matrix to the n-th power with `mat_pow`, then read off `result[0][1]` for `F(n)`. Each matrix multiply is O(1) (fixed 2×2 size) and there are O(log n) of them.

**Q: Modular exponentiation under a non-prime modulus?**
The same algorithm works: iterate bits of n, squaring and multiplying mod m at each step. The caveat is that modular inverse (needed for negative exponents) only exists when `gcd(a, m) = 1`; use `extgcd` to compute it rather than Fermat's little theorem, which requires a prime modulus.

---

## RECALL

Fast exponentiation computes `x^n` in O(log n) multiplications by bit-decomposing n and accumulating: square `x` at each bit position; multiply into the result when the bit is set. Signal: `pow(x, n)` for huge n; "x^n mod m"; linear-recurrence speedup via matrix exponentiation (Fibonacci in O(log n)). Pitfalls: take modulus after every multiply (not just at the end); copy input matrix before mutating; `M^0 = I` (identity, not zero matrix).

```python
from typing import Optional


def pow_int(x: int, n: int) -> int:
    result, cur = 1, x
    while n:
        if n & 1:
            result *= cur
        cur *= cur
        n >>= 1
    return result


def pow_mod(x: int, n: int, mod: int) -> int:
    result, cur = 1 % mod, x % mod
    while n:
        if n & 1:
            result = result * cur % mod
        cur = cur * cur % mod
        n >>= 1
    return result


def mat_mult(A, B, mod=None):
    k = len(A)
    C = [[0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            s = sum(A[i][t] * B[t][j] for t in range(k))
            C[i][j] = s % mod if mod is not None else s
    return C


def mat_pow(M, n, mod=None):
    k = len(M)
    result = [[int(i == j) for j in range(k)] for i in range(k)]
    cur = [row[:] for row in M]
    while n:
        if n & 1:
            result = mat_mult(result, cur, mod)
        cur = mat_mult(cur, cur, mod)
        n >>= 1
    return result
```
