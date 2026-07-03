#!/usr/bin/env python3
"""Extract a Feeding Frenzy 2 .saf archive.

    python3 unpack.py FF2.saf out/

Archive layout (little-endian):

    header   char magic[4] = "FFAS"; u32 version; u32 toc_offset;
    data     raw concatenation of every packed file
    toc      u32 version; u8 global_checksum[16]; u32 entry_count;
             entry_count * {
                 u32 data_start, data_size;
                 u8  checksum[16];
                 u16 path_len;
                 char path[path_len];   // e.g. "resource/...\0"
             }
"""

import os
import sys
import struct

MAGIC = b'FFAS'


def read_toc(buf):
    if buf[:4] != MAGIC:
        raise ValueError('not a FFAS/.saf archive')
    toc_off = struct.unpack_from('<I', buf, 8)[0]
    p = toc_off
    version, = struct.unpack_from('<I', buf, p); p += 4
    global_checksum = buf[p:p + 16]; p += 16
    count, = struct.unpack_from('<I', buf, p); p += 4

    entries = []
    for _ in range(count):
        data_start, data_size = struct.unpack_from('<II', buf, p); p += 8
        checksum = buf[p:p + 16]; p += 16
        path_len, = struct.unpack_from('<H', buf, p); p += 2
        path = buf[p:p + path_len]; p += path_len
        entries.append((data_start, data_size, checksum, path))
    return version, global_checksum, entries


def main(argv):
    if len(argv) != 3:
        sys.exit('usage: unpack.py <archive.saf> <output_dir>')
    archive, out_dir = argv[1], argv[2]

    buf = open(archive, 'rb').read()
    _, _, entries = read_toc(buf)

    for data_start, data_size, _checksum, path in entries:
        rel = path.rstrip(b'\x00').decode('ascii')
        dest = os.path.join(out_dir, *rel.split('/'))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as fh:
            fh.write(buf[data_start:data_start + data_size])

    print('extracted %d files to %s' % (len(entries), out_dir))


if __name__ == '__main__':
    main(sys.argv)
