# Feeding Frenzy 2 `.saf` tooling

Unpack and repack the single asset archive (`FF2.saf`) that PopCap's *Feeding
Frenzy 2* (2006) ships all its sprites, sounds, and cutscenes in.

The interesting part isn't the container format — it's that the archive is
self-checksumming. Every file and the table of contents carry a 16-byte digest
that the engine recomputes on load. It's MD5 to the letter (same sine table,
rotations, and padding) **except** the four initialization words were swapped,
so a stock `hashlib.md5()` produces valid-length but wrong digests and repacks
get rejected. The real init vector was recovered from `ff2.exe`; see
[`nmd5.py`](nmd5.py). A short write-up is in [`article.tex`](article.tex).

## Archive format

```
header   char magic[4] = "FFAS"; u32 version; u32 toc_offset;    // little-endian
data     raw concatenation of every packed file
toc      u32 version; u8 global_checksum[16]; u32 entry_count;
         entry_count * {
             u32  data_start, data_size;
             u8   checksum[16];          // custom-IV MD5 of the file bytes
             u16  path_len;
             char path[path_len];        // e.g. "resource/actors/...\0"
         }
```

The global checksum is the custom-IV MD5 of `entry_count` followed by each
entry's `(data_start, data_size, checksum, path_len, path)`. A Kaitai Struct
description of the container is in [`saf.ksy`](saf.ksy).

## Usage

```sh
python3 unpack.py FF2.saf out/          # -> out/resource/...
python3 pack.py   out/resource FF2.saf  # rebuilds a valid, moddable archive
```

Round-tripping the original archive reproduces every per-file checksum and the
global checksum exactly, so a repacked tree loads in the game unmodified. Edit a
sprite or an XML layout in `out/resource/` before repacking to mod the game.

## Files

| File | What |
|------|------|
| `nmd5.py`   | Custom-init-vector MD5 (the checksum the engine expects) |
| `unpack.py` | Extract a `.saf` to a directory |
| `pack.py`   | Repack a directory into a `.saf` |
| `saf.ksy`   | Kaitai Struct spec for the container format |
| `article.tex` / `article.pdf` | Paged Out! write-up |

The game, its archive, and its extracted assets are copyrighted by PopCap and
are excluded via `.gitignore` — bring your own copy.
