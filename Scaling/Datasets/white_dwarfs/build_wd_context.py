"""Formal context of the 40 pc white-dwarf sample (O'Brien et al. 2024, CDS J/MNRAS/527/8687).
Objects: all 1078 white dwarfs of table A1 (version of 14 Nov 2024). Binarity from table A6."""
import re, csv, sys, os
from parse import read_a1, read_a6
DATA = sys.argv[1] if len(sys.argv) > 1 else 'data'
A = read_a1(os.path.join(DATA, 'tablea1.dat'))
B = read_a6(os.path.join(DATA, 'tablea6.dat'))

# ---- spectral type decomposition (Sion et al. 1983 letters) ----
def letters(sp):
    core = sp.replace('pec', '').replace('(warm)', '').replace(':', '').strip()
    core = core[1:] if core.startswith('D') else core
    return core
def primary(sp): return letters(sp)[:1]
def has(sp, ch): return ch in re.sub(r'[^A-Z]', '', letters(sp))
def secondary_has(sp, ch): return ch in re.sub(r'[^A-Z]', '', letters(sp))[1:]

# ---- wide binaries (table A6) ----
comp = {}   # Gaia id -> set of companion kinds
for b in B:
    kinds = re.findall(r'WD|MS|BD', b['BinType'])          # first is the WD itself
    ids = [b['Id1'], b['Id2'], b['Id3']]
    for pos, gid in enumerate(ids):
        if not gid: continue
        others = kinds[:pos] + kinds[pos + 1:] if pos < len(kinds) else kinds[1:]
        comp.setdefault(gid, set()).update(others)
        comp.setdefault(gid + '#n', set()).add(len(kinds))
def wide(a): return a['Gaia'] in comp
def wide_has(a, k): return k in comp.get(a['Gaia'], set())
def wide_n(a): return max(comp.get(a['Gaia'] + '#n', {0}))

UNRESOLVED = re.compile(r'Double degenerate|triple degenerate|non-single-star', re.I)
M, T, AGE = 'Massc', 'Teffc', 'Agec'      # values after the low-mass correction (adopted in the paper)
gt = lambda a, k, x: a[k] is not None and a[k] > x
lt = lambda a, k, x: a[k] is not None and a[k] < x

ATTR = [
 # S1 spectral features
 ('hydrogen lines (A)',              lambda a: has(a['SpType'], 'A')),
 ('helium lines (B)',                lambda a: has(a['SpType'], 'B')),
 ('featureless spectrum (DC)',       lambda a: primary(a['SpType']) == 'C'),
 ('carbon features (Q)',             lambda a: has(a['SpType'], 'Q')),
 ('metal lines (Z, polluted)',       lambda a: has(a['SpType'], 'Z')),
 ('magnetic (H or P)',               lambda a: secondary_has(a['SpType'], 'H') or secondary_has(a['SpType'], 'P')),
 ('emission lines (e)',              lambda a: bool(re.search(r'e$', a['SpType'].replace('pec', '')))),
 ('peculiar, warm or uncertain type',      lambda a: 'pec' in a['SpType'] or ':' in a['SpType'] or primary(a['SpType']) == 'X' or '(warm)' in a['SpType']),
 # S2 atmosphere / fit
 ('hydrogen-dominated atmosphere (fit)', lambda a: a['Comp'] == 'H'),
 ('Gaia parameters available',       lambda a: a[M] is not None and a[T] is not None),
 ('IR-faint (collision-induced absorption)', lambda a: a['Com'].startswith('IR-faint')),
 # S3 mass (interordinal)
 ('mass < 0.45 Msun (low mass)',     lambda a: lt(a, M, 0.45)),
 ('mass > 0.9 Msun (massive)',       lambda a: gt(a, M, 0.9)),
 ('mass > 1.1 Msun (ultramassive)',  lambda a: gt(a, M, 1.1)),
 # S4 temperature (ordinal)
 ('Teff > 5000 K',                   lambda a: gt(a, T, 5000)),
 ('Teff > 10500 K',                  lambda a: gt(a, T, 10500)),
 ('Teff > 12500 K',                  lambda a: gt(a, T, 12500)),
 # S5 cooling age (ordinal, decades)
 ('cooling age > 0.1 Gyr',           lambda a: gt(a, AGE, 0.1)),
 ('cooling age > 1 Gyr',             lambda a: gt(a, AGE, 1.0)),
 ('cooling age > 10 Gyr',            lambda a: gt(a, AGE, 10.0)),
 # S6 binarity
 ('in wide binary or multiple (A6)', wide),
 ('wide main-sequence companion',    lambda a: wide_has(a, 'MS')),
 ('wide white-dwarf companion',      lambda a: wide_has(a, 'WD')),
 ('wide brown-dwarf companion',      lambda a: wide_has(a, 'BD')),
 ('wide system with >=3 members',    lambda a: wide_n(a) >= 3),
 ('unresolved binary evidence (DD or Gaia orbit)', lambda a: bool(UNRESOLVED.search(a['Com']))),
 # S7 observational
 ('within 20 pc',                    lambda a: a['Plx'] >= 50.0),
 ('within 10 pc',                    lambda a: a['Plx'] >= 100.0),
]
objs = [a['Name'] for a in A]
assert len(set(objs)) == len(objs)
inc = [[bool(f(a)) for _, f in ATTR] for a in A]
with open('wd40pc.cxt', 'w') as f:
    f.write('B\n\n%d\n%d\n\n' % (len(objs), len(ATTR)))
    f.write('\n'.join(objs) + '\n' + '\n'.join(n for n, _ in ATTR) + '\n')
    for r in inc: f.write(''.join('X' if v else '.' for v in r) + '\n')
with open('wd40pc_source.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['name', 'gaia_dr3', 'parallax_mas', 'distance_pc', 'abs_G', 'bp_rp', 'spectral_type', 'fit_composition',
                'teff_corrected_K', 'mass_corrected_Msun', 'cooling_age_Gyr', 'wide_companions', 'wide_system_size', 'comment'])
    for a in A:
        w.writerow([a['Name'], a['Gaia'], a['Plx'], round(1000 / a['Plx'], 3), a['GMAG'], a['BPRP'], a['SpType'], a['Comp'],
                    a[T], a[M], a[AGE], '+'.join(sorted(comp.get(a['Gaia'], []))), wide_n(a) or '', a['Com']])
print(len(objs), 'objects x', len(ATTR), 'attributes; distinct rows', len({tuple(r) for r in inc}))
for j, (n, _) in enumerate(ATTR): print(f'{sum(r[j] for r in inc):5d}  {n}')
