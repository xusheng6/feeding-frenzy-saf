#!/usr/bin/env python3
"""Repack a directory tree into a Feeding Frenzy 2 .saf archive.

    python3 pack.py out/resource FF2.saf

The engine validates the archive on load, so every per-file checksum and the
global checksum are recomputed with the game's custom-init MD5 (see nmd5.py).
The stored path keeps the given directory's name as its prefix, matching the
original archive (paths look like "resource/actors/...").
"""

import os
import sys
import struct

import nmd5

MAGIC = b'FFAS'
VERSION = 1
HEADER_SIZE = 0xC  # magic + version + toc_offset


def collect(root):
    """Yield (stored_path, data) for every file under ``root``.

    Paths are stored relative to ``root``'s parent and slash-separated, so a
    tree rooted at ``.../resource`` yields ``resource/...`` entries.
    """
    base = os.path.dirname(os.path.abspath(root))
    for dirpath, _dirs, files in os.walk(root):
        for name in sorted(files):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, base).replace(os.sep, '/')
            with open(full, 'rb') as fh:
                yield rel, fh.read()


def build(root):
    data = bytearray()
    entries = []  # (data_start, data_size, checksum, path_bytes_with_nul)

    for rel, blob in collect(root):
        start = HEADER_SIZE + len(data)
        data += blob
        path = rel.encode('ascii') + b'\x00'
        entries.append((start, len(blob), nmd5.md5(blob), path))

    toc_offset = HEADER_SIZE + len(data)

    # Global checksum: entry_count followed by each entry's fields.
    gbuf = bytearray(struct.pack('<I', len(entries)))
    for start, size, checksum, path in entries:
        gbuf += struct.pack('<II', start, size) + checksum
        gbuf += struct.pack('<H', len(path)) + path
    global_checksum = nmd5.md5(bytes(gbuf))

    out = bytearray()
    out += MAGIC + struct.pack('<II', VERSION, toc_offset)
    out += data
    out += struct.pack('<I', VERSION) + global_checksum
    out += struct.pack('<I', len(entries))
    for start, size, checksum, path in entries:
        out += struct.pack('<II', start, size) + checksum
        out += struct.pack('<H', len(path)) + path
    return bytes(out), len(entries)


def main(argv):
    if len(argv) != 3:
        sys.exit('usage: pack.py <input_dir> <output.saf>')
    root, output = argv[1], argv[2]

    blob, count = build(root)
    with open(output, 'wb') as fh:
        fh.write(blob)
    print('packed %d files into %s (%d bytes)' % (count, output, len(blob)))


if __name__ == '__main__':
    main(sys.argv)
