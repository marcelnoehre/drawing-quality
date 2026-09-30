"""Reconstruct the 10 pc sample v2 (Reylé et al. 2022 update; CDS J/A+A/650/A201, Aug 2023)
from v1 (Reylé et al. 2021) using the change list published in the v2 paper (Sect. 2),
then cross-check against the first 343 rows of the v2 CSV."""
import csv, json, sys

v1 = list(csv.DictReader(open('data/tenpc_v1.csv')))
assert len(v1) == 540, len(v1)

REMOVE = {  # Reylé et al. 2022, Sect. 2.2
    '2MASS J16471580+5632057', '2MASS J07584037+3247245',
    'CFBDS J213926+022023 A', 'CFBDS J213926+022023 B',
    '41 Ara Ab', 'GJ 748 A', 'GJ 748 B', 'SZ UMa B',
    'UPM J0815-2344 B', 'WISE J081117.81-805141.3'}
rows = [dict(r) for r in v1 if r['OBJ_NAME'] not in REMOVE]
assert len(rows) == 530, len(rows)

def find(name):
    return next(r for r in rows if r['OBJ_NAME'] == name)

# renames to v2 naming
find('Lalande 21185 b')['OBJ_NAME'] = 'HD 95735 b'
find('41 Ara B')['OBJ_NAME'] = '41 Ara Ba'
# Sect. 3.1: Gaia DR3 two-body orbits confirm low-mass-star nature of GJ 1230 C and GJ 867 C
find('GJ 1230 C')['OBJ_CAT'] = 'LM'
find('GJ 867 C')['OBJ_CAT'] = 'LM'

def add_after(host, new):
    i = rows.index(find(host))
    rows.insert(i + 1, new)

def planet(host, name):
    h = find(host)
    return dict(NB_OBJ='v2', NB_SYS=h['NB_SYS'], SYSTEM_NAME=h['SYSTEM_NAME'], OBJ_CAT='Planet',
                OBJ_NAME=name, SP_TYPE='', SIMBAD_NAME='', COMMON_NAME='', G='', G_EST='', DIST=h['DIST'])

# Sect. 2.1 additions: 8 planets
add_after('HD 95735 b', planet('HD 95735', 'HD 95735 c'))
add_after('LTT 1445 A b', planet('BD-17 588 A', 'LTT 1445 A c'))
add_after('BD+01 2447', planet('BD+01 2447', 'BD+01 2447 b'))
add_after('BD+11 2576', planet('BD+11 2576', 'BD+11 2576 b'))
add_after('CD-45 5378', planet('CD-45 5378', 'GJ 367 b'))
add_after('HD 260655', planet('HD 260655', 'HD 260655 c'))
add_after('HD 260655', planet('HD 260655', 'HD 260655 b'))
add_after('Wolf 1069', planet('Wolf 1069', 'Wolf 1069 b'))
# companion to GJ 666 B (= 41 Ara B) from Gaia DR3 astrometric orbit (0.17-0.73 Msun)
b = find('41 Ara Ba')
add_after('41 Ara Ba', dict(b, NB_OBJ='v2', OBJ_CAT='LM?', OBJ_NAME='41 Ara Bb', SP_TYPE='', G='', G_EST=''))
# two brown dwarfs, new systems
rows.append(dict(NB_OBJ='v2', NB_SYS='v2a', SYSTEM_NAME='CWISEP J225628.97+400227.3', OBJ_CAT='BD',
                 OBJ_NAME='CWISEP J225628.97+400227.3', SP_TYPE='Y?', SIMBAD_NAME='', COMMON_NAME='',
                 G='', G_EST='est', DIST='9.5'))
rows.append(dict(NB_OBJ='v2', NB_SYS='v2b', SYSTEM_NAME='CWISEP J181006.00-101001.1', OBJ_CAT='BD',
                 OBJ_NAME='CWISEP J181006.00-101001.1', SP_TYPE='esdT0', SIMBAD_NAME='', COMMON_NAME='',
                 G='', G_EST='est', DIST='8.9'))

planets = [r for r in rows if r['OBJ_CAT'] == 'Planet']
bodies = [r for r in rows if r['OBJ_CAT'] != 'Planet']
systems = {r['NB_SYS'] for r in rows}
print('entries', len(rows), 'bodies', len(bodies), 'planets', len(planets), 'systems', len(systems))
cats = {}
for r in bodies: cats[r['OBJ_CAT']] = cats.get(r['OBJ_CAT'], 0) + 1
print(cats)

# ---- cross-check with v2 head (rows 1..343, ordered by distance) ----
head = [l.rstrip('\n').split('|') for l in open('data/tenpc_v2_head.psv') if l.strip()]
norm = lambda s: s.replace('.0', '') if s[:1] in 'FGK' else s
recon = {r['OBJ_NAME']: r for r in rows}
alias = {'Legget A': 'GJ 661 A'}
problems = 0
for cat, name, sp in head[:-1]:
    n = alias.get(name, name)
    r = recon.get(n)
    if r is None:
        print('MISSING in reconstruction:', cat, name); problems += 1; continue
    if r['OBJ_CAT'] != cat or norm(r['SP_TYPE']) != norm(sp):
        print('DIFF', name, (r['OBJ_CAT'], r['SP_TYPE']), 'vs v2', (cat, sp)); problems += 1
# every reconstructed object nearer than 61 Vir must appear in head
headnames = {alias.get(n, n) for _, n, _ in head}
for r in rows:
    if r['NB_OBJ'] != 'v2' and float(r['DIST']) < 8.52 and r['OBJ_NAME'] not in headnames:
        print('EXTRA in reconstruction (not in v2 head):', r['OBJ_NAME'], r['DIST']); problems += 1
print('cross-check problems:', problems)
json.dump(rows, open('tenpc_v2_reconstructed.json', 'w'), indent=0)
