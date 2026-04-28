"""Sieve of Eratosthenes templates. Full reference: topics/math/sieve.md."""
import math


def sieve(n: int) -> list[int]:
    """Return all primes <= n."""
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
    """Return SPF table of length n+1; spf[0]=spf[1]=0 (sentinel)."""
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
