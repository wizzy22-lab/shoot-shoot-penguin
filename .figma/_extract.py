#!/usr/bin/env python3
"""Dump a Figma node subtree (from the saved get_node_info JSON) with
coordinates relative to the section origin, plus render-relevant attrs.

Usage: python3 .figma/_extract.py <nodeId> [maxdepth]
"""
import json, sys

TREE = '/Users/wizzy/.claude/projects/-Users-wizzy-Desktop--SHOOT-SHOOT-PENGUIN/95648dd0-398b-4939-9c7a-c798bc7a32dd/tool-results/mcp-figma-get_node_info-1782726010270.txt'

def load():
    return json.load(open(TREE))

def find(node, nid):
    if node.get('id') == nid:
        return node
    for c in node.get('children', []):
        r = find(c, nid)
        if r:
            return r
    return None

def box(n):
    b = n.get('absoluteBoundingBox') or {}
    return b.get('x'), b.get('y'), b.get('width'), b.get('height')

def fillinfo(n):
    fs = n.get('fills')
    if not isinstance(fs, list):
        return ''
    parts = []
    for f in fs:
        if not isinstance(f, dict):
            continue
        t = f.get('type')
        if t == 'IMAGE':
            parts.append('IMG:' + str(f.get('imageRef', ''))[:8])
        elif t and 'GRADIENT' in t:
            parts.append('GRAD:' + t)
        elif t == 'SOLID':
            o = f.get('opacity')
            parts.append('SOLID' + (f'@{o}' if o not in (None, 1) else ''))
    return ','.join(parts)

def main():
    nid = sys.argv[1]
    maxd = int(sys.argv[2]) if len(sys.argv) > 2 else 99
    root = load()
    sec = find(root, nid)
    if not sec:
        print('NOT FOUND', nid); return
    sx, sy, sw, sh = box(sec)
    print(f'SECTION {sec.get("name")} {sec.get("type")} {nid}  w={sw} h={sh}  origin=({sx},{sy})')
    print('=' * 100)

    def rel(n):
        x, y, w, h = box(n)
        if x is None:
            return None
        return round(x - sx, 1), round(y - sy, 1), w, h

    def walk(n, depth=0):
        if depth > maxd:
            return
        r = rel(n)
        ind = '  ' * depth
        st = n.get('style') or {}
        font = ''
        if st:
            font = f"{st.get('fontFamily')} {st.get('fontStyle')} {st.get('fontSize')}/{st.get('lineHeightPx')} ls={round(st.get('letterSpacing',0),2)} {st.get('textAlignHorizontal')}"
        extra = []
        if n.get('cornerRadius') is not None:
            extra.append(f"r={n.get('cornerRadius')}")
        if n.get('rectangleCornerRadii'):
            extra.append(f"rr={n.get('rectangleCornerRadii')}")
        sw_ = n.get('strokeWeight')
        if sw_:
            extra.append(f"stroke={sw_}")
        op = n.get('opacity')
        if op not in (None, 1):
            extra.append(f"op={op}")
        fi = fillinfo(n)
        if fi:
            extra.append(f"fill={fi}")
        if n.get('layoutMode'):
            extra.append(f"AL={n.get('layoutMode')} gap={n.get('itemSpacing')} pad={n.get('paddingTop')},{n.get('paddingRight')},{n.get('paddingBottom')},{n.get('paddingLeft')}")
        pos = f"({r[0]},{r[1]} {r[2]}x{r[3]})" if r else "(-)"
        line = f"{ind}{n.get('type'):<9} {pos:<26} {n.get('name')!r}"
        if extra:
            line += '  [' + ' '.join(extra) + ']'
        print(line)
        if n.get('type') == 'TEXT':
            txt = n.get('characters', '')
            print(f"{ind}   TXT {font}")
            print(f"{ind}   = {txt!r}")
        for c in n.get('children', []):
            walk(c, depth + 1)

    walk(sec, 0)

main()
