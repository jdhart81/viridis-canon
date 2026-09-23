"""viridis_fn — shared runtime for Viridis OS reference runners (Python stdlib only).

Every callable function in the canon ships a ``runner.py`` exposing
``run(inputs: dict) -> dict``.  Runners import this module for three things:

1. **JavaScript-number semantics.**  The public product computes receipts in
   JavaScript.  To keep receipts bit-for-bit reproducible across languages and
   host C libraries, the transcendental functions here are exact ports of the
   fdlibm implementations shipped in V8 12.4 (``src/base/ieee754.cc``), which is
   what Node.js 22 uses for ``Math.exp/expm1/log/cosh/pow`` and ``**``.  They do
   not depend on the platform ``libm``.  ``to_fixed`` reproduces
   ``Number(x.toFixed(places))`` and ``locale_usd`` reproduces
   ``toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2})``.
2. **Closed-schema input validation** with the same messages the product uses.
3. **Honest error classes**: ``InputError`` for a caller mistake; anything else
   is a runner fault.

Nothing here reads the network, the clock, the environment or the filesystem.
"""

from __future__ import annotations

import math
import struct
from decimal import ROUND_HALF_UP, Context, Decimal
from typing import Any

__all__ = [
    "InputError",
    "validate_schema",
    "num",
    "opt",
    "to_fixed",
    "round12",
    "is_close",
    "lexically_less",
    "js_div",
    "js_pow",
    "js_exp",
    "js_expm1",
    "js_log",
    "js_cosh",
    "js_sqrt",
    "js_max",
    "js_min",
    "js_sum",
    "locale_usd",
    "LN2",
    "KB",
]

KB = 1.380649e-23
# Exact decimal context: every finite double has <= 767 significant digits.
_EXACT = Context(prec=1100, Emax=999999, Emin=-999999)


class InputError(ValueError):
    """Caller supplied inputs outside the function's declared domain."""


# ---------------------------------------------------------------------------
# IEEE-754 word access (fdlibm macros)
# ---------------------------------------------------------------------------

def _bits(d: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", d))[0]


def _from_bits(b: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", b & 0xFFFFFFFFFFFFFFFF))[0]


def _i32(v: int) -> int:
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


def _u32(v: int) -> int:
    return v & 0xFFFFFFFF


def _hi(d: float) -> int:  # signed high word
    return _i32(_bits(d) >> 32)


def _lo(d: float) -> int:  # unsigned low word
    return _bits(d) & 0xFFFFFFFF


def _insert(hi: int, lo: int) -> float:
    return _from_bits((_u32(hi) << 32) | _u32(lo))


def _set_hi(d: float, v: int) -> float:
    return _from_bits((_bits(d) & 0x00000000FFFFFFFF) | (_u32(v) << 32))


def _set_lo(d: float, v: int) -> float:
    return _from_bits((_bits(d) & 0xFFFFFFFF00000000) | _u32(v))


_INF = float("inf")
_NAN = float("nan")


def js_div(a: float, b: float) -> float:
    """IEEE division (JavaScript ``/``): never raises."""
    a = float(a)
    b = float(b)
    if b == 0.0:
        if a == 0.0 or math.isnan(a):
            return _NAN
        neg = (math.copysign(1.0, a) < 0) != (math.copysign(1.0, b) < 0)
        return -_INF if neg else _INF
    return a / b


def _mul(a: float, b: float) -> float:
    # Python float multiplication already follows IEEE (inf on overflow).
    return a * b


# ---------------------------------------------------------------------------
# fdlibm ports (V8 12.4 base::ieee754)
# ---------------------------------------------------------------------------

_EXP_HALF = (0.5, -0.5)
_LN2HI = (6.93147180369123816490e-01, -6.93147180369123816490e-01)
_LN2LO = (1.90821492927058770002e-10, -1.90821492927058770002e-10)


def js_exp(x: float) -> float:
    x = float(x)
    one = 1.0
    o_threshold = 7.09782712893383973096e02
    u_threshold = -7.45133219101941108420e02
    invln2 = 1.44269504088896338700e00
    P1 = 1.66666666666666019037e-01
    P2 = -2.77777777770155933842e-03
    P3 = 6.61375632143793436117e-05
    P4 = -1.65339022054652515390e-06
    P5 = 4.13813679705723846039e-08
    E = 2.718281828459045
    huge = 1.0e300
    twom1000 = 9.33263618503218878990e-302
    two1023 = 8.988465674311579539e307

    hi = 0.0
    lo = 0.0
    k = 0
    hx = _u32(_hi(x))
    xsb = (hx >> 31) & 1
    hx &= 0x7FFFFFFF

    if hx >= 0x40862E42:
        if hx >= 0x7FF00000:
            lx = _lo(x)
            if ((hx & 0xFFFFF) | lx) != 0:
                return x + x
            return x if xsb == 0 else 0.0
        if x > o_threshold:
            return huge * huge
        if x < u_threshold:
            return twom1000 * twom1000

    if hx > 0x3FD62E42:
        if hx < 0x3FF0A2B2:
            if x == 1.0:
                return E
            hi = x - _LN2HI[xsb]
            lo = _LN2LO[xsb]
            k = 1 - xsb - xsb
        else:
            k = int(invln2 * x + _EXP_HALF[xsb])  # C truncation toward zero
            t = float(k)
            hi = x - t * _LN2HI[0]
            lo = t * _LN2LO[0]
        x = hi - lo
    elif hx < 0x3E300000:
        if huge + x > one:
            return one + x
    else:
        k = 0

    t = x * x
    if k >= -1021:
        twopk = _insert(0x3FF00000 + _i32(_u32(k) << 20), 0)
    else:
        twopk = _insert(0x3FF00000 + _u32(_u32(k + 1000) << 20), 0)
    c = x - t * (P1 + t * (P2 + t * (P3 + t * (P4 + t * P5))))
    if k == 0:
        return one - ((x * c) / (c - 2.0) - x)
    y = one - ((lo - (x * c) / (2.0 - c)) - hi)
    if k >= -1021:
        if k == 1024:
            return y * 2.0 * two1023
        return y * twopk
    return y * twopk * twom1000


def js_expm1(x: float) -> float:
    x = float(x)
    one = 1.0
    tiny = 1.0e-300
    o_threshold = 7.09782712893383973096e02
    ln2_hi = 6.93147180369123816490e-01
    ln2_lo = 1.90821492927058770002e-10
    invln2 = 1.44269504088896338700e00
    Q1 = -3.33333333333331316428e-02
    Q2 = 1.58730158725481460165e-03
    Q3 = -7.93650757867487942473e-05
    Q4 = 4.00821782732936239552e-06
    Q5 = -2.01099218183624371326e-07
    huge = 1.0e300

    hx = _u32(_hi(x))
    xsb = hx & 0x80000000
    hx &= 0x7FFFFFFF

    if hx >= 0x4043687A:
        if hx >= 0x40862E42:
            if hx >= 0x7FF00000:
                low = _lo(x)
                if ((hx & 0xFFFFF) | low) != 0:
                    return x + x
                return x if xsb == 0 else -1.0
            if x > o_threshold:
                return huge * huge
        if xsb != 0:
            if x + tiny < 0.0:
                return tiny - one

    if hx > 0x3FD62E42:
        if hx < 0x3FF0A2B2:
            if xsb == 0:
                hi = x - ln2_hi
                lo = ln2_lo
                k = 1
            else:
                hi = x + ln2_hi
                lo = -ln2_lo
                k = -1
        else:
            k = int(invln2 * x + (0.5 if xsb == 0 else -0.5))
            t = float(k)
            hi = x - t * ln2_hi
            lo = t * ln2_lo
        x = hi - lo
        c = (hi - x) - lo
    elif hx < 0x3C900000:
        t = huge + x
        return x - (t - (huge + x))
    else:
        k = 0
        c = 0.0

    hfx = 0.5 * x
    hxs = x * hfx
    r1 = one + hxs * (Q1 + hxs * (Q2 + hxs * (Q3 + hxs * (Q4 + hxs * Q5))))
    t = 3.0 - r1 * hfx
    e = hxs * ((r1 - t) / (6.0 - x * t))
    if k == 0:
        return x - (x * e - hxs)
    twopk = _insert(0x3FF00000 + _i32(_u32(k) << 20), 0)
    e = x * (e - c) - c
    e -= hxs
    if k == -1:
        return 0.5 * (x - e) - 0.5
    if k == 1:
        if x < -0.25:
            return -2.0 * (e - (x + 0.5))
        return one + 2.0 * (x - e)
    if k <= -2 or k > 56:
        y = one - (e - x)
        if k == 1024:
            y = y * 2.0 * 8.98846567431158e307
        else:
            y = y * twopk
        return y - one
    t = one
    if k < 20:
        t = _set_hi(t, 0x3FF00000 - (0x200000 >> k))
        y = t - (e - x)
        y = y * twopk
    else:
        t = _set_hi(t, (0x3FF - k) << 20)
        y = x - (e + t)
        y += one
        y = y * twopk
    return y


def js_log(x: float) -> float:
    x = float(x)
    ln2_hi = 6.93147180369123816490e-01
    ln2_lo = 1.90821492927058770002e-10
    two54 = 1.80143985094819840000e16
    Lg1 = 6.666666666666735130e-01
    Lg2 = 3.999999999940941908e-01
    Lg3 = 2.857142874366239149e-01
    Lg4 = 2.222219843214978396e-01
    Lg5 = 1.818357216161805012e-01
    Lg6 = 1.531383769920937332e-01
    Lg7 = 1.479819860511658591e-01
    zero = 0.0

    hx = _hi(x)
    lx = _lo(x)
    k = 0
    if hx < 0x00100000:
        if ((hx & 0x7FFFFFFF) | lx) == 0:
            return -_INF
        if hx < 0:
            return _NAN
        k -= 54
        x *= two54
        hx = _hi(x)
    if hx >= 0x7FF00000:
        return x + x
    k += (hx >> 20) - 1023
    hx &= 0x000FFFFF
    i = (hx + 0x95F64) & 0x100000
    x = _set_hi(x, hx | (i ^ 0x3FF00000))
    k += i >> 20
    f = x - 1.0
    if (0x000FFFFF & (2 + hx)) < 3:
        if f == zero:
            if k == 0:
                return zero
            dk = float(k)
            return dk * ln2_hi + dk * ln2_lo
        R = f * f * (0.5 - 0.33333333333333333 * f)
        if k == 0:
            return f - R
        dk = float(k)
        return dk * ln2_hi - ((R - dk * ln2_lo) - f)
    s = f / (2.0 + f)
    dk = float(k)
    z = s * s
    i = hx - 0x6147A
    w = z * z
    j = 0x6B851 - hx
    t1 = w * (Lg2 + w * (Lg4 + w * Lg6))
    t2 = z * (Lg1 + w * (Lg3 + w * (Lg5 + w * Lg7)))
    i |= j
    R = t2 + t1
    if i > 0:
        hfsq = 0.5 * f * f
        if k == 0:
            return f - (hfsq - s * (hfsq + R))
        return dk * ln2_hi - ((hfsq - (s * (hfsq + R) + dk * ln2_lo)) - f)
    if k == 0:
        return f - s * (f - R)
    return dk * ln2_hi - ((s * (f - R) - dk * ln2_lo) - f)


def js_cosh(x: float) -> float:
    x = float(x)
    KCOSH_OVERFLOW = 710.4758600739439
    one = 1.0
    half = 0.5
    huge = 1.0e300
    ix = _hi(x) & 0x7FFFFFFF
    if ix < 0x3FD62E43:
        t = js_expm1(abs(x))
        w = one + t
        if ix < 0x3C800000:
            return w
        return one + (t * t) / (w + w)
    if ix < 0x40360000:
        t = js_exp(abs(x))
        return half * t + half / t
    if ix < 0x40862E42:
        return half * js_exp(abs(x))
    if abs(x) <= KCOSH_OVERFLOW:
        w = js_exp(half * abs(x))
        t = half * w
        return t * w
    if ix >= 0x7FF00000:
        return x * x
    return huge * huge


def js_sqrt(x: float) -> float:
    x = float(x)
    if math.isnan(x) or x < 0:
        return _NAN
    return math.sqrt(x)


_BP = (1.0, 1.5)
_DP_H = (0.0, 5.84962487220764160156e-01)
_DP_L = (0.0, 1.35003920212974897128e-08)


def js_pow(x: float, y: float) -> float:
    """``Math.pow`` / ``**`` exactly as V8 12.4 (fdlibm e_pow.c)."""
    x = float(x)
    y = float(y)
    zero = 0.0
    one = 1.0
    two = 2.0
    two53 = 9007199254740992.0
    huge = 1.0e300
    tiny = 1.0e-300
    L1 = 5.99999999999994648725e-01
    L2 = 4.28571428578550184252e-01
    L3 = 3.33333329818377432918e-01
    L4 = 2.72728123808534006489e-01
    L5 = 2.30660745775561754067e-01
    L6 = 2.06975017800338417784e-01
    P1 = 1.66666666666666019037e-01
    P2 = -2.77777777770155933842e-03
    P3 = 6.61375632143793436117e-05
    P4 = -1.65339022054652515390e-06
    P5 = 4.13813679705723846039e-08
    lg2 = 6.93147180559945286227e-01
    lg2_h = 6.93147182464599609375e-01
    lg2_l = -1.90465429995776804525e-09
    ovt = 8.0085662595372944372e-17
    cp = 9.61796693925975554329e-01
    cp_h = 9.61796700954437255859e-01
    cp_l = -7.02846165095275826516e-09
    ivln2 = 1.44269504088896338700e00
    ivln2_h = 1.44269502162933349609e00
    ivln2_l = 1.92596299112661746887e-08

    hx = _hi(x)
    lx = _lo(x)
    hy = _hi(y)
    ly = _lo(y)
    ix = hx & 0x7FFFFFFF
    iy = hy & 0x7FFFFFFF

    if (iy | ly) == 0:
        return one
    if ix > 0x7FF00000 or (ix == 0x7FF00000 and lx != 0) or iy > 0x7FF00000 or (
        iy == 0x7FF00000 and ly != 0
    ):
        return x + y

    yisint = 0
    if hx < 0:
        if iy >= 0x43400000:
            yisint = 2
        elif iy >= 0x3FF00000:
            k = (iy >> 20) - 0x3FF
            if k > 20:
                j = _i32(ly >> (52 - k))
                if _i32(j << (52 - k)) == _i32(ly):
                    yisint = 2 - (j & 1)
            elif ly == 0:
                j = iy >> (20 - k)
                if _i32(j << (20 - k)) == iy:
                    yisint = 2 - (j & 1)

    if ly == 0:
        if iy == 0x7FF00000:
            if ((ix - 0x3FF00000) | lx) == 0:
                return y - y
            if ix >= 0x3FF00000:
                return y if hy >= 0 else zero
            return -y if hy < 0 else zero
        if iy == 0x3FF00000:
            if hy < 0:
                return js_div(one, x)
            return x
        if hy == 0x40000000:
            return x * x
        if hy == 0x3FE00000:
            if hx >= 0:
                return js_sqrt(x)

    ax = abs(x)
    if lx == 0:
        if ix == 0x7FF00000 or ix == 0 or ix == 0x3FF00000:
            z = ax
            if hy < 0:
                z = js_div(one, z)
            if hx < 0:
                if ((ix - 0x3FF00000) | yisint) == 0:
                    z = _NAN
                elif yisint == 1:
                    z = -z
            return z

    n = (hx >> 31) + 1
    if (n | yisint) == 0:
        return _NAN

    s = one
    if (n | (yisint - 1)) == 0:
        s = -one

    if iy > 0x41E00000:
        if iy > 0x43F00000:
            if ix <= 0x3FEFFFFF:
                return huge * huge if hy < 0 else tiny * tiny
            if ix >= 0x3FF00000:
                return huge * huge if hy > 0 else tiny * tiny
        if ix < 0x3FEFFFFF:
            return s * huge * huge if hy < 0 else s * tiny * tiny
        if ix > 0x3FF00000:
            return s * huge * huge if hy > 0 else s * tiny * tiny
        t = ax - one
        w = (t * t) * (0.5 - t * (0.3333333333333333333333 - t * 0.25))
        u = ivln2_h * t
        v = t * ivln2_l - w * ivln2
        t1 = u + v
        t1 = _set_lo(t1, 0)
        t2 = v - (t1 - u)
    else:
        n = 0
        if ix < 0x00100000:
            ax *= two53
            n -= 53
            ix = _hi(ax)
        n += (ix >> 20) - 0x3FF
        j = ix & 0x000FFFFF
        ix = j | 0x3FF00000
        if j <= 0x3988E:
            k = 0
        elif j < 0xBB67A:
            k = 1
        else:
            k = 0
            n += 1
            ix -= 0x00100000
        ax = _set_hi(ax, ix)

        u = ax - _BP[k]
        v = js_div(one, ax + _BP[k])
        ss = u * v
        s_h = _set_lo(ss, 0)
        t_h = _set_hi(zero, ((ix >> 1) | 0x20000000) + 0x00080000 + (k << 18))
        t_l = ax - (t_h - _BP[k])
        s_l = v * ((u - s_h * t_h) - s_h * t_l)
        s2 = ss * ss
        r = s2 * s2 * (L1 + s2 * (L2 + s2 * (L3 + s2 * (L4 + s2 * (L5 + s2 * L6)))))
        r += s_l * (s_h + ss)
        s2 = s_h * s_h
        t_h = 3.0 + s2 + r
        t_h = _set_lo(t_h, 0)
        t_l = r - ((t_h - 3.0) - s2)
        u = s_h * t_h
        v = s_l * t_h + t_l * ss
        p_h = u + v
        p_h = _set_lo(p_h, 0)
        p_l = v - (p_h - u)
        z_h = cp_h * p_h
        z_l = cp_l * p_h + p_l * cp + _DP_L[k]
        t = float(n)
        t1 = ((z_h + z_l) + _DP_H[k]) + t
        t1 = _set_lo(t1, 0)
        t2 = z_l - (((t1 - t) - _DP_H[k]) - z_h)

    y1 = _set_lo(y, 0)
    p_l = (y - y1) * t1 + y * t2
    p_h = y1 * t1
    z = p_l + p_h
    j = _hi(z)
    i = _lo(z)
    if j >= 0x40900000:
        if ((j - 0x40900000) | i) != 0:
            return s * huge * huge
        if p_l + ovt > z - p_h:
            return s * huge * huge
    elif (j & 0x7FFFFFFF) >= 0x4090CC00:
        if _u32(j) != 0xC090CC00 or i != 0:
            return s * tiny * tiny
        if p_l <= z - p_h:
            return s * tiny * tiny

    i = j & 0x7FFFFFFF
    k = (i >> 20) - 0x3FF
    n = 0
    if i > 0x3FE00000:
        n = j + (0x00100000 >> (k + 1))
        k = ((n & 0x7FFFFFFF) >> 20) - 0x3FF
        t = _set_hi(zero, n & ~(0x000FFFFF >> k))
        n = ((n & 0x000FFFFF) | 0x00100000) >> (20 - k)
        if j < 0:
            n = -n
        p_h -= t
    t = p_l + p_h
    t = _set_lo(t, 0)
    u = t * lg2_h
    v = (p_l - (t - p_h)) * lg2 + t * lg2_l
    z = u + v
    w = v - (z - u)
    t = z * z
    t1 = z - t * (P1 + t * (P2 + t * (P3 + t * (P4 + t * P5))))
    r = js_div(z * t1, (t1 - two) - (w + z * w))
    z = one - (r - z)
    j = _hi(z)
    j = _i32(j + _i32(_u32(n) << 20))
    if (j >> 20) <= 0:
        z = math.ldexp(z, n)
    else:
        z = _set_hi(z, _hi(z) + _i32(_u32(n) << 20))
    return s * z


LN2 = js_log(2.0)


# ---------------------------------------------------------------------------
# JavaScript Number helpers
# ---------------------------------------------------------------------------

def to_fixed(value: float, places: int = 12) -> float:
    """``Number(value.toFixed(places))`` (ECMA-262 Number.prototype.toFixed)."""
    x = float(value)
    if math.isnan(x) or math.isinf(x):
        return x
    if abs(x) >= 1e21:
        return x
    sign = ""
    if x < 0:
        sign = "-"
        x = -x
    q = Decimal(x).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP, context=_EXACT)
    return float(sign + format(q, "f"))


def round12(value: float) -> float:
    return to_fixed(value, 12)


def is_close(left: float, right: float) -> bool:
    return abs(left - right) <= max(1e-15, 1e-12 * max(abs(left), abs(right)))


def lexically_less(left: list, right: list) -> bool:
    for index in range(min(len(left), len(right))):
        if left[index] != right[index]:
            return left[index] < right[index]
    return len(left) < len(right)


def js_max(*values: float) -> float:
    """``Math.max`` including NaN propagation and +0 > -0."""
    result = -_INF
    for v in values:
        v = float(v)
        if math.isnan(v):
            return _NAN
        if v > result or (v == 0.0 and result == 0.0 and math.copysign(1.0, result) < 0):
            result = v
    return result


def js_min(*values: float) -> float:
    result = _INF
    for v in values:
        v = float(v)
        if math.isnan(v):
            return _NAN
        if v < result or (v == 0.0 and result == 0.0 and math.copysign(1.0, v) < 0):
            result = v
    return result


def js_sum(values) -> float:
    """Left-to-right ``reduce((s, v) => s + v, 0)``."""
    total = 0.0
    for v in values:
        total = total + float(v)
    return total


def locale_usd(value: float) -> str:
    """``value.toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2})``.

    ECMA-402 (ICU) first converts the double to its *shortest round-trip*
    decimal string and then rounds that decimal half away from zero
    ("halfExpand") — unlike ``toFixed``, which rounds the exact binary value.
    """
    x = float(value)
    if math.isnan(x):
        return "NaN"
    if math.isinf(x):
        return "-∞" if x < 0 else "∞"
    q = Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP, context=_EXACT)
    negative = q < 0
    text = format(abs(q), ",f")
    if negative and q != 0:
        return "-" + text
    return text


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def num(inputs: dict, key: str) -> float:
    return float(inputs[key])


def opt(inputs: dict, key: str, default: Any = None) -> Any:
    if key in inputs and inputs[key] is not None:
        return float(inputs[key])
    return default


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _fmt(value: Any) -> str:
    """JavaScript ``String(value)`` for the numbers used in schema bounds."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e21:
        return str(int(value))
    return repr(value)


def validate_schema(value: Any, schema: dict, path: str = "inputs") -> None:
    """Closed JSON-schema subset with the exact messages of the product validator."""
    kind = schema.get("type")
    if kind == "object":
        if not isinstance(value, dict):
            raise InputError(f"{path} must be an object")
        properties = schema.get("properties", {})
        missing = [key for key in schema.get("required", []) if key not in value]
        if missing:
            raise InputError(f"{path} missing required field(s): {', '.join(missing)}")
        if schema.get("additionalProperties") is False:
            extra = sorted(key for key in value if key not in properties)
            if extra:
                raise InputError(f"{path} contains unsupported field(s): {', '.join(extra)}")
        for key, child in properties.items():
            if key in value:
                validate_schema(value[key], child, f"{path}.{key}")
        return
    if kind == "array":
        if not isinstance(value, list):
            raise InputError(f"{path} must be an array")
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise InputError(f"{path} must contain at least {schema['minItems']} item(s)")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise InputError(f"{path} must contain at most {schema['maxItems']} item(s)")
        if "items" in schema:
            for index, item in enumerate(value):
                validate_schema(item, schema["items"], f"{path}[{index}]")
        return
    if kind == "number" and not _is_number(value):
        raise InputError(f"{path} must be a finite number")
    if kind == "integer" and not (_is_number(value) and float(value).is_integer()):
        raise InputError(f"{path} must be an integer")
    if kind == "string" and not isinstance(value, str):
        raise InputError(f"{path} must be a string")
    if kind == "boolean" and not isinstance(value, bool):
        raise InputError(f"{path} must be a boolean")
    if "enum" in schema:
        allowed = schema["enum"]
        if not any(value == item and isinstance(value, bool) == isinstance(item, bool) for item in allowed):
            raise InputError(f"{path} must be one of {', '.join(_fmt(item) for item in allowed)}")
    if _is_number(value):
        if "minimum" in schema and value < schema["minimum"]:
            raise InputError(f"{path} must be >= {_fmt(schema['minimum'])}")
        if "maximum" in schema and value > schema["maximum"]:
            raise InputError(f"{path} must be <= {_fmt(schema['maximum'])}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise InputError(f"{path} must be > {_fmt(schema['exclusiveMinimum'])}")
        if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
            raise InputError(f"{path} must be < {_fmt(schema['exclusiveMaximum'])}")


# ---------------------------------------------------------------------------
# Checkable conditions (hypotheses / conclusions)
# ---------------------------------------------------------------------------
#
# A manifest states each hypothesis and conclusion as a small expression over
# the declared inputs (and, for conclusions, previously derived values), e.g.
# ``"delta_mu > 0"`` or ``"all(0 <= f <= 1 for f in alignment_factors)"``.
# The grammar is a whitelisted subset of Python expressions: literals, names,
# arithmetic, comparisons, boolean logic, conditional expressions, subscripts,
# single-generator comprehensions and the functions in ``_CHECK_FUNCTIONS``.
# Arithmetic uses the same JavaScript-number semantics as the runners.

import ast as _ast
import operator as _operator

_BINOPS = {
    _ast.Add: _operator.add,
    _ast.Sub: _operator.sub,
    _ast.Mult: _operator.mul,
    _ast.Div: js_div,
    _ast.Pow: js_pow,
}
_CMPOPS = {
    _ast.Lt: _operator.lt,
    _ast.LtE: _operator.le,
    _ast.Gt: _operator.gt,
    _ast.GtE: _operator.ge,
    _ast.Eq: _operator.eq,
    _ast.NotEq: _operator.ne,
    _ast.In: lambda a, b: a in b,
    _ast.NotIn: lambda a, b: a not in b,
    _ast.Is: _operator.is_,
    _ast.IsNot: _operator.is_not,
}


def _prod(values) -> float:
    total = 1.0
    for v in values:
        total = total * float(v)
    return total


def real_log(x: float) -> float:
    """Mathlib ``Real.log``: log |x| for x != 0 and 0 at 0 (total, never NaN)."""
    x = float(x)
    if x == 0.0 or math.isnan(x):
        return 0.0
    return js_log(abs(x))


def logb(base: float, x: float) -> float:
    """Mathlib ``Real.logb b x = Real.log x / Real.log b``."""
    return js_div(real_log(x), real_log(base))


def nat_sub(a: float, b: float) -> float:
    """Truncated subtraction on naturals (Lean ``Nat.sub``)."""
    return js_max(0.0, float(a) - float(b))


_TOL = 1e-9


def approx_le(a: float, b: float, scale: float = 1.0) -> bool:
    """``a <= b`` up to a relative floating-point tolerance (conclusion side only)."""
    a = float(a)
    b = float(b)
    return a <= b + _TOL * max(1.0, abs(a), abs(b), abs(float(scale)))


def approx_eq(a: float, b: float, scale: float = 1.0) -> bool:
    a = float(a)
    b = float(b)
    return abs(a - b) <= _TOL * max(1.0, abs(a), abs(b), abs(float(scale)))


_CHECK_FUNCTIONS = {
    "len": len,
    "all": all,
    "any": any,
    "abs": abs,
    "min": js_min,
    "max": js_max,
    "sum": js_sum,
    "prod": _prod,
    "sqrt": js_sqrt,
    "log": js_log,
    "exp": js_exp,
    "is_close": is_close,
    "range": range,
    "sorted": sorted,
    "float": float,
    "int": int,
    "round12": round12,
    "real_log": real_log,
    "logb": logb,
    "nat_sub": nat_sub,
    "approx_le": approx_le,
    "approx_eq": approx_eq,
    "pow": js_pow,
}
_ALLOWED_NODES = (
    _ast.Expression, _ast.BoolOp, _ast.And, _ast.Or, _ast.BinOp, _ast.UnaryOp,
    _ast.Not, _ast.USub, _ast.UAdd, _ast.Compare, _ast.Name, _ast.Load, _ast.Constant,
    _ast.Call, _ast.Subscript, _ast.Index if hasattr(_ast, "Index") else _ast.Constant,
    _ast.GeneratorExp, _ast.ListComp, _ast.comprehension, _ast.Store, _ast.IfExp,
    _ast.List, _ast.Tuple, _ast.Slice,
    *_BINOPS.keys(), *_CMPOPS.keys(),
)


class CheckSyntaxError(ValueError):
    """A manifest condition uses syntax outside the checkable-condition grammar."""


def parse_check(expression: str) -> _ast.Expression:
    try:
        tree = _ast.parse(expression, mode="eval")
    except SyntaxError as error:  # pragma: no cover - message path
        raise CheckSyntaxError(f"cannot parse condition {expression!r}: {error.msg}") from None
    for node in _ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise CheckSyntaxError(f"condition {expression!r} uses unsupported syntax {type(node).__name__}")
        if isinstance(node, _ast.Call):
            if not isinstance(node.func, _ast.Name) or node.func.id not in _CHECK_FUNCTIONS:
                raise CheckSyntaxError(f"condition {expression!r} calls a function outside the whitelist")
            if node.keywords:
                raise CheckSyntaxError(f"condition {expression!r} uses keyword arguments")
        if isinstance(node, _ast.Name) and node.id.startswith("_"):
            raise CheckSyntaxError(f"condition {expression!r} uses a private name")
        if isinstance(node, _ast.comprehension) and (node.ifs or node.is_async):
            raise CheckSyntaxError(f"condition {expression!r} uses a filtered comprehension")
    return tree


def condition_names(expression: str) -> set:
    tree = parse_check(expression)
    bound = {n.target.id for n in _ast.walk(tree) if isinstance(n, _ast.comprehension) and isinstance(n.target, _ast.Name)}
    return {n.id for n in _ast.walk(tree) if isinstance(n, _ast.Name) and n.id not in _CHECK_FUNCTIONS and n.id not in bound}


def _eval(node, env):
    if isinstance(node, _ast.Expression):
        return _eval(node.body, env)
    if isinstance(node, _ast.Constant):
        return node.value
    if isinstance(node, _ast.Name):
        if node.id in env:
            return env[node.id]
        if node.id in _CHECK_FUNCTIONS:
            return _CHECK_FUNCTIONS[node.id]
        if node.id in ("true", "false", "null"):
            return {"true": True, "false": False, "null": None}[node.id]
        return None  # an optional input that was not supplied
    if isinstance(node, _ast.BoolOp):
        if isinstance(node.op, _ast.And):
            result = True
            for value in node.values:
                result = _eval(value, env)
                if not result:
                    return result
            return result
        result = False
        for value in node.values:
            result = _eval(value, env)
            if result:
                return result
        return result
    if isinstance(node, _ast.UnaryOp):
        operand = _eval(node.operand, env)
        if isinstance(node.op, _ast.Not):
            return not operand
        if isinstance(node.op, _ast.USub):
            return -operand
        return +operand
    if isinstance(node, _ast.BinOp):
        left = _eval(node.left, env)
        right = _eval(node.right, env)
        if isinstance(left, (int, float)) and not isinstance(left, bool):
            left = float(left)
        if isinstance(right, (int, float)) and not isinstance(right, bool):
            right = float(right)
        return _BINOPS[type(node.op)](left, right)
    if isinstance(node, _ast.Compare):
        left = _eval(node.left, env)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval(comparator, env)
            if not _CMPOPS[type(op)](left, right):
                return False
            left = right
        return True
    if isinstance(node, _ast.IfExp):
        return _eval(node.body, env) if _eval(node.test, env) else _eval(node.orelse, env)
    if isinstance(node, _ast.Call):
        func = _CHECK_FUNCTIONS[node.func.id]
        args = [_eval(arg, env) for arg in node.args]
        return func(*args)
    if isinstance(node, _ast.Subscript):
        value = _eval(node.value, env)
        index = _eval(node.slice, env)
        if isinstance(index, float) and index.is_integer():
            index = int(index)
        return value[index]
    if isinstance(node, _ast.Slice):
        return slice(
            None if node.lower is None else int(_eval(node.lower, env)),
            None if node.upper is None else int(_eval(node.upper, env)),
        )
    if isinstance(node, (_ast.List, _ast.Tuple)):
        return [_eval(item, env) for item in node.elts]
    if isinstance(node, (_ast.GeneratorExp, _ast.ListComp)):
        generator = node.generators[0]
        iterable = _eval(generator.iter, env)
        results = []
        for item in iterable:
            scope = dict(env)
            _bind(generator.target, item, scope)
            results.append(_eval(node.elt, scope))
        return results
    raise CheckSyntaxError(f"unsupported node {type(node).__name__}")  # pragma: no cover


def _bind(target, value, scope):
    if isinstance(target, _ast.Name):
        scope[target.id] = value
        return
    if isinstance(target, _ast.Tuple):
        for sub, item in zip(target.elts, value):
            _bind(sub, item, scope)
        return
    raise CheckSyntaxError("unsupported comprehension target")


def evaluate(expression: str, env: dict):
    """Evaluate a manifest expression against ``env`` (inputs plus derived values)."""
    return _eval(parse_check(expression), env)


def check(expression: str, env: dict) -> bool:
    """Evaluate a manifest condition; ``None`` (missing optional input) is False."""
    try:
        return bool(evaluate(expression, env))
    except (TypeError, ValueError, IndexError, KeyError, ZeroDivisionError):
        return False
