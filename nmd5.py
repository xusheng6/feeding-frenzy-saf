"""Feeding Frenzy 2's checksum: standard MD5 with non-standard init constants.

The engine validates its .saf archive with what looks like MD5 -- same 64 sine
constants, same rotation schedule, same padding -- but the four initialization
words have been swapped. Feeding a stock hashlib.md5() the archive bytes yields
a digest of the right length that never matches, so repacks get rejected.

The real init vector, lifted out of ff2.exe:

    A = 0xfb132803   (stock MD5: 0x67452301)
    B = 0x06e828f3               0xefcdab89
    C = 0xa12a051c               0x98badcfe
    D = 0x9bedf4fc               0x10325476

Everything below is a textbook MD5 parameterised on that vector.
"""

import struct
import math

FF_IV = (0xfb132803, 0x06e828f3, 0xa12a051c, 0x9bedf4fc)
STOCK_IV = (0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476)

# Per-operation left-rotation amounts (RFC 1321).
_S = ([7, 12, 17, 22] * 4 + [5, 9, 14, 20] * 4 +
      [4, 11, 16, 23] * 4 + [6, 10, 15, 21] * 4)
# Binary-integer-part-of sine table (RFC 1321).
_K = [int(abs(math.sin(i + 1)) * 2 ** 32) & 0xffffffff for i in range(64)]


def _rol(x, c):
    x &= 0xffffffff
    return ((x << c) | (x >> (32 - c))) & 0xffffffff


def md5(data, iv=FF_IV):
    """Return the 16-byte MD5 digest of ``data`` using init vector ``iv``."""
    a0, b0, c0, d0 = iv

    msg = bytearray(data)
    bit_len = (8 * len(data)) & 0xffffffffffffffff
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0)
    msg += struct.pack('<Q', bit_len)

    for off in range(0, len(msg), 64):
        M = struct.unpack('<16I', msg[off:off + 64])
        a, b, c, d = a0, b0, c0, d0
        for i in range(64):
            if i < 16:
                f, g = (b & c) | (~b & d), i
            elif i < 32:
                f, g = (d & b) | (~d & c), (5 * i + 1) % 16
            elif i < 48:
                f, g = b ^ c ^ d, (3 * i + 5) % 16
            else:
                f, g = c ^ (b | ~d), (7 * i) % 16
            f = (f + a + _K[i] + M[g]) & 0xffffffff
            a, d, c = d, c, b
            b = (b + _rol(f, _S[i])) & 0xffffffff
        a0 = (a0 + a) & 0xffffffff
        b0 = (b0 + b) & 0xffffffff
        c0 = (c0 + c) & 0xffffffff
        d0 = (d0 + d) & 0xffffffff

    return struct.pack('<4I', a0, b0, c0, d0)
