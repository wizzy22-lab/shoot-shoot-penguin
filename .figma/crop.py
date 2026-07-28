#!/usr/bin/env python3
"""Crop a vertical row band from a PNG (pure stdlib, no PIL).
Usage: python3 .figma/crop.py <in.png> <out.png> <y0> <y1>
Handles 8-bit truecolour (RGB) and truecolour+alpha (RGBA) PNGs.
"""
import sys, zlib, struct

def read_chunks(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    i = 8
    chunks = []
    while i < len(data):
        ln = struct.unpack('>I', data[i:i+4])[0]
        typ = data[i+4:i+8]
        body = data[i+8:i+8+ln]
        chunks.append((typ, body))
        i += 12 + ln
    return chunks

def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
    if pa <= pb and pa <= pc: return a
    if pb <= pc: return b
    return c

def main():
    inp, outp, y0, y1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    data = open(inp, 'rb').read()
    chunks = read_chunks(data)
    ihdr = dict(zip(('w','h','bd','ct','cm','fm','im'),
                    struct.unpack('>IIBBBBB', next(b for t,b in chunks if t==b'IHDR'))))
    w, h, ct, bd = ihdr['w'], ihdr['h'], ihdr['ct'], ihdr['bd']
    assert bd == 8 and ct in (2, 6), f'unsupported bd={bd} ct={ct}'
    bpp = 3 if ct == 2 else 4
    raw = zlib.decompress(b''.join(b for t,b in chunks if t==b'IDAT'))
    stride = w * bpp
    # unfilter
    rows = []
    prev = bytearray(stride)
    pos = 0
    for _ in range(h):
        f = raw[pos]; pos += 1
        line = bytearray(raw[pos:pos+stride]); pos += stride
        if f == 1:
            for x in range(bpp, stride): line[x] = (line[x] + line[x-bpp]) & 255
        elif f == 2:
            for x in range(stride): line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x-bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x-bpp] if x >= bpp else 0
                c = prev[x-bpp] if x >= bpp else 0
                line[x] = (line[x] + paeth(a, prev[x], c)) & 255
        rows.append(line)
        prev = line
    y0 = max(0, y0); y1 = min(h, y1)
    out_rows = rows[y0:y1]
    # re-filter with None
    buf = bytearray()
    for line in out_rows:
        buf.append(0); buf += line
    comp = zlib.compress(bytes(buf), 9)
    def chunk(typ, body):
        return struct.pack('>I', len(body)) + typ + body + struct.pack('>I', zlib.crc32(typ+body) & 0xffffffff)
    new_ihdr = struct.pack('>IIBBBBB', w, len(out_rows), 8, ct, 0, 0, 0)
    out = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', new_ihdr) + chunk(b'IDAT', comp) + chunk(b'IEND', b'')
    open(outp, 'wb').write(out)
    print(f'cropped {inp} rows {y0}:{y1} -> {outp} ({w}x{len(out_rows)})')

main()
