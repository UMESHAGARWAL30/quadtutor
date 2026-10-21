def check_root(a: float, b: float, c: float, x: float, tol: float = 1e-6) -> bool:
    """True if x satisfies a*x^2 + b*x + c = 0."""
    return abs(a * x * x + b * x + c) < tol

def discriminant(a: float, b: float, c: float) -> float:
    return b * b - 4 * a * c

def nature_of_roots(a: float, b: float, c: float) -> str:
    d = discriminant(a, b, c)
    if d > 0: return "two distinct real roots"
    if d == 0: return "two equal real roots"
    return "no real roots"