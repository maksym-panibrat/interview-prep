"""Fast exponentiation templates. Full reference: topics/math/fast-exponentiation.md."""
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
