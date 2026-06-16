from itertools import combinations, product

regions = [
    ['A', 'A', 'B', 'B'],
    ['A', 'A', 'B', 'B'],
    ['C', 'C', 'D', 'D'],
    ['C', 'C', 'D', 'D'],
]
rows = 4
cols = 4
stars = 2

valid_row_combos = [tuple(sel) for sel in combinations(range(cols), stars) if all(abs(sel[i] - sel[i-1]) > 1 for i in range(1, len(sel)))]
print('valid row combos', valid_row_combos)

solutions = 0
for rowsel in product(valid_row_combos, repeat=rows):
    ok = True
    for r in range(1, rows):
        for c in rowsel[r]:
            if any((c + dc) in rowsel[r-1] for dc in (-1, 0, 1)):
                ok = False
                break
        if not ok:
            break
    if not ok:
        continue
    colcount = [0] * cols
    for r in rowsel:
        for c in r:
            colcount[c] += 1
    if any(cc != stars for cc in colcount):
        continue
    region_counts = {}
    for rowidx, r in enumerate(rowsel):
        for c in r:
            lab = regions[rowidx][c]
            region_counts[lab] = region_counts.get(lab, 0) + 1
    if any(count != stars for count in region_counts.values()):
        continue
    solutions += 1
    print('solution', rowsel)
print('solutions', solutions)
