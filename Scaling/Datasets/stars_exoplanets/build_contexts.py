"""Build two formal contexts (Burmeister .cxt) from the 10 pc sample v2 (Reylé et al. 2021/2022).
Context 1: all 456 stars, brown dwarfs and white dwarfs.   Context 2: all 85 confirmed exoplanets."""
import json, re, csv
rows = json.load(open('tenpc_v2_reconstructed.json'))
PP = {p['name']: p for p in json.load(open('planet_params.json'))}

# ---------- helpers ----------
CONST = set('And Ant Aps Aqr Aql Ara Ari Aur Boo Cae Cam Cnc CVn CMa CMi Cap Car Cas Cen Cep Cet Cha Cir Col Com CrA CrB Crv Crt Cru Cyg Del Dor Dra Equ Eri For Gem Gru Her Hor Hya Hyi Ind Lac Leo LMi Lep Lib Lup Lyn Lyr Men Mic Mon Mus Nor Oct Oph Ori Pav Peg Per Phe Pic Psc PsA Pup Pyx Ret Sge Sgr Sco Scl Sct Ser Sex Tau Tel Tri TrA Tuc UMa UMi Vel Vir Vol Vul'.split())
def is_gcvs(name):
    if not name: return False
    name = re.sub(r'\s[A-D][ab]?$', '', name.strip())          # strip component suffix
    m = re.fullmatch(r'(V\d{3,4}|[A-Z]{1,2})\s(\w{3})', name)
    if not m or m.group(2) not in CONST: return False
    l = m.group(1)
    if l.startswith('V') and l[1:].isdigit(): return True
    if 'J' in l: return False
    if len(l) == 1: return l >= 'R'
    return l[1] >= l[0]                                          # RR..ZZ, AA..QZ

# Reylé et al. 2022 (v2 paper) Sect. 3.2: objects classified as variable in Gaia DR3
# (solar-like, short-timescale, rotational modulation). GJ 15 A/B excluded: they appear in the
# variability tables only because of GAPS photometry, not because variability was detected.
GAIA_VAR = {'GJ 625','AN Sex','GJ 1151','L 49-19','G 19-7','MCC 135','BD+43 2796','BD+16 2708 A','HD 100623 B',
            'Ross 248','DENIS J104814.6-395606','GJ 643','GJ 486','L 173-19','LP 655-48','BD+61 195 B','GJ 867 B'}
CLS = 'OBAFGKMLTY'
def sptval(sp):
    """numeric position on the OBAFGKMLTY sequence (class*10 + subtype); None if absent/WD"""
    if not sp or sp.startswith('D'): return None
    m = re.search(r'([OBAFGKMLTY])\s*(\d+(?:\.\d+)?)?', sp.replace('esd', '').replace('sd', ''))
    if not m: return None
    return CLS.index(m.group(1)) * 10 + (float(m.group(2)) if m.group(2) else 0.0)

bodies = [r for r in rows if r['OBJ_CAT'] != 'Planet']
planets = [r for r in rows if r['OBJ_CAT'] == 'Planet']
sysmem = {}
for r in bodies: sysmem.setdefault(r['NB_SYS'], []).append(r)
def mag(r):
    for k in ('G', 'G_EST'):
        try: return float(r[k])
        except: pass
    return None
def primary(sysid):
    cand = [o for o in sysmem[sysid] if mag(o) is not None]
    if not cand: return None
    return min(cand, key=lambda o: (mag(o), sptval(o['SP_TYPE']) if sptval(o['SP_TYPE']) is not None else 99, o['OBJ_NAME']))
# planet -> host (nearest preceding body in same system; LTT 1445 A c explicit)
host_of = {}
for i, r in enumerate(rows):
    if r['OBJ_CAT'] != 'Planet': continue
    j = i - 1
    while rows[j]['OBJ_CAT'] == 'Planet' or rows[j]['NB_SYS'] != r['NB_SYS']: j -= 1
    host_of[r['OBJ_NAME']] = rows[j]['OBJ_NAME']
host_of['LTT 1445 A c'] = 'BD-17 588 A'
planets_of = {}
for p, h in host_of.items(): planets_of.setdefault(h, []).append(p)

# ---------- Kopparapu et al. (2014) conservative habitable zone ----------
def seff(teff, s0, a, b, c, d):
    t = teff - 5780.0
    return s0 + a*t + b*t**2 + c*t**3 + d*t**4
def hz_edges(teff):
    inner = seff(teff, 1.107, 1.332e-4, 1.580e-8, -8.308e-12, -1.931e-15)   # runaway greenhouse, 1 Earth mass
    outer = seff(teff, 0.356, 6.171e-5, 1.698e-9, -3.198e-12, -5.575e-16)   # maximum greenhouse
    return inner, outer
def planet_derived(p):
    d = PP[p]
    inner, outer = hz_edges(d['teff'])
    return dict(above_outer=d['insol'] > outer, above_inner=d['insol'] > inner, inner=inner, outer=outer)

# ---------- context 1: stars / brown dwarfs / white dwarfs ----------
SA = [  # (attribute name, function)
 ('hydrogen-burning star',        lambda r: r['OBJ_CAT'] in ('*', 'LM', 'LM?')),
 ('brown dwarf',                  lambda r: r['OBJ_CAT'] in ('BD', 'BD?')),
 ('white dwarf',                  lambda r: r['OBJ_CAT'] in ('WD', 'WD?')),
 ('class unconfirmed (candidate)',lambda r: r['OBJ_CAT'].endswith('?')),
 ('SpT on OBAFGKMLTY sequence',   lambda r: sptval(r['SP_TYPE']) is not None),
 ('SpT G or later',               lambda r: (sptval(r['SP_TYPE']) or -1) >= 40),
 ('SpT K or later',               lambda r: (sptval(r['SP_TYPE']) or -1) >= 50),
 ('SpT M or later',               lambda r: (sptval(r['SP_TYPE']) or -1) >= 60),
 ('SpT M3.5 or later (fully convective)', lambda r: (sptval(r['SP_TYPE']) or -1) >= 63.5),
 ('SpT M7 or later (ultracool)',  lambda r: (sptval(r['SP_TYPE']) or -1) >= 67),
 ('SpT L or later',               lambda r: (sptval(r['SP_TYPE']) or -1) >= 70),
 ('SpT T or later',               lambda r: (sptval(r['SP_TYPE']) or -1) >= 80),
 ('SpT Y',                        lambda r: (sptval(r['SP_TYPE']) or -1) >= 90),
 ('subdwarf (sd/esd, metal-poor)',lambda r: bool(re.match(r'e?sd', r['SP_TYPE'] or ''))),
 ('emission-line flag (e) in SpT',lambda r: bool(re.search(r'[OBAFGKMLTY]\d*(\.\d+)?e', r['SP_TYPE'] or ''))),
 ('Gaia DR3 variable (Reyle+2022)', lambda r: r['OBJ_NAME'] in GAIA_VAR),
 ('WD spectral type known',       lambda r: (r['SP_TYPE'] or '').startswith('D')),
 ('WD hydrogen atmosphere (DA)',  lambda r: (r['SP_TYPE'] or '').startswith('DA')),
 ('WD metal lines (Z)',           lambda r: (r['SP_TYPE'] or '').startswith('D') and 'Z' in re.sub(r'[^A-Z]', '', r['SP_TYPE'][1:])),
 ('WD carbon features (Q)',       lambda r: (r['SP_TYPE'] or '').startswith('D') and 'Q' in re.sub(r'[^A-Z]', '', r['SP_TYPE'][1:])),
 ('WD featureless (DC)',          lambda r: (r['SP_TYPE'] or '').startswith('DC')),
 ('WD magnetic (P/H)',            lambda r: (r['SP_TYPE'] or '').startswith('D') and bool(re.search(r'[PH]', re.sub(r'[^A-Z]', '', r['SP_TYPE'][2:])))),
 ('member of multiple system',    lambda r: len(sysmem[r['NB_SYS']]) >= 2),
 ('member of system with >=3 bodies', lambda r: len(sysmem[r['NB_SYS']]) >= 3),
 ('primary (brightest) of multiple system', lambda r: len(sysmem[r['NB_SYS']]) >= 2 and r is primary(r['NB_SYS'])),
 ('has hydrogen-burning companion', lambda r: any(o is not r and o['OBJ_CAT'] in ('*', 'LM', 'LM?') for o in sysmem[r['NB_SYS']])),
 ('has brown-dwarf companion',    lambda r: any(o is not r and o['OBJ_CAT'] in ('BD', 'BD?') for o in sysmem[r['NB_SYS']])),
 ('has white-dwarf companion',    lambda r: any(o is not r and o['OBJ_CAT'] in ('WD', 'WD?') for o in sysmem[r['NB_SYS']])),
 ('hosts confirmed planet',       lambda r: len(planets_of.get(r['OBJ_NAME'], [])) >= 1),
 ('hosts >=2 confirmed planets',  lambda r: len(planets_of.get(r['OBJ_NAME'], [])) >= 2),
 ('hosts transiting planet',      lambda r: any(PP[p]['transiting'] for p in planets_of.get(r['OBJ_NAME'], []))),
 ('hosts planet in conservative HZ', lambda r: any(planet_derived(p)['above_outer'] and not planet_derived(p)['above_inner']
                                              for p in planets_of.get(r['OBJ_NAME'], []))),
 ('member of planet-hosting system', lambda r: any(o['OBJ_NAME'] in planets_of for o in sysmem[r['NB_SYS']])),
 ('within 5 pc',                  lambda r: float(r['DIST']) <= 5.0),
 ('G magnitude measured by Gaia', lambda r: r['G'] not in ('', None)),
]
host_row = {r['OBJ_NAME']: r for r in bodies}
star_attr = {name: f for name, f in SA}

# ---------- context 2: exoplanets ----------
MJ = 317.828
def H(p, attr): return star_attr[attr](host_row[host_of[p]])
PA = [
 ('mass > 2.04 Earth (above Terran regime)',   lambda p: PP[p]['mass_e'] > 2.04),
 ('mass > 0.414 Jupiter (Jovian regime)',      lambda p: PP[p]['mass_e'] > 0.414 * MJ),
 ('only minimum mass (m sin i) known',         lambda p: PP[p]['mass_prov'].startswith('Msini')),
 ('ultra-short period (P < 1 d)',              lambda p: PP[p]['P'] < 1.0),
 ('instellation above HZ outer edge',          lambda p: planet_derived(p)['above_outer']),
 ('instellation above HZ inner edge',          lambda p: planet_derived(p)['above_inner']),
 ('discovered by radial velocity',             lambda p: (PP[p]['method'] or '').lower().startswith(('radial', 'rv'))),
 ('transits its host',                         lambda p: PP[p]['transiting']),
 ('in multi-planet system',                    lambda p: len(planets_of[host_of[p]]) >= 2),
 ('host in multiple-star system',              lambda p: H(p, 'member of multiple system')),
 ('host SpT M',                                lambda p: H(p, 'SpT M or later')),
 ('host fully convective (M3.5 or later)',     lambda p: H(p, 'SpT M3.5 or later (fully convective)')),
 ('host SpT has emission-line flag (e)',       lambda p: H(p, 'emission-line flag (e) in SpT')),
 ('host within 5 pc',                          lambda p: H(p, 'within 5 pc')),
 ('in NASA Exoplanet Archive composite (2026)',lambda p: PP[p]['in_nasa_2026']),
 ('flagged controversial in NASA archive',     lambda p: PP[p].get('controv') == '1'),
]

def write_cxt(path, objs, attrs, incidence):
    assert len(set(objs)) == len(objs), 'duplicate object names'
    with open(path, 'w') as f:
        f.write('B\n\n%d\n%d\n\n' % (len(objs), len(attrs)))
        for o in objs: f.write(o + '\n')
        for a in attrs: f.write(a + '\n')
        for row in incidence: f.write(''.join('X' if v else '.' for v in row) + '\n')

S_objs = [r['OBJ_NAME'] for r in bodies]
S_inc = [[bool(f(r)) for _, f in SA] for r in bodies]
write_cxt('tenpc_stars.cxt', S_objs, [a for a, _ in SA], S_inc)
P_objs = [r['OBJ_NAME'] for r in planets]
P_inc = [[bool(f(p)) for _, f in PA] for p in P_objs]
write_cxt('tenpc_exoplanets.cxt', P_objs, [a for a, _ in PA], P_inc)

# many-valued source tables for transparency
with open('tenpc_stars_source.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['object', 'system', 'catalogue_class', 'spectral_type', 'G', 'G_estimated', 'distance_pc', 'n_system_bodies', 'planets'])
    for r in bodies: w.writerow([r['OBJ_NAME'], r['SYSTEM_NAME'], r['OBJ_CAT'], r['SP_TYPE'], r['G'], r['G_EST'], r['DIST'], len(sysmem[r['NB_SYS']]), ';'.join(planets_of.get(r['OBJ_NAME'], []))])
with open('tenpc_exoplanets_source.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['planet', 'host', 'mass_earth', 'mass_type', 'period_d', 'a_AU', 'instellation_Searth', 'host_Teff', 'HZ_inner_S', 'HZ_outer_S', 'discovery_method', 'transiting', 'in_NASA_2026', 'NASA_controversial', 'parameter_source'])
    for p in P_objs:
        d = PP[p]; z = planet_derived(p)
        w.writerow([p, host_of[p], round(d['mass_e'], 3), d['mass_prov'], d['P'], d['a'], round(d['insol'], 4), d['teff'], round(z['inner'], 3), round(z['outer'], 3), d['method'], d['transiting'], d['in_nasa_2026'], d.get('controv'), d['src'] + ('; S ' + d['insol_src'] if d.get('insol_src') else '')])

# report
for name, objs, attrs, inc in (('stars', S_objs, [a for a, _ in SA], S_inc), ('exoplanets', P_objs, [a for a, _ in PA], P_inc)):
    print('\n==', name, len(objs), 'objects x', len(attrs), 'attributes; distinct rows:', len({tuple(r) for r in inc}))
    for j, a in enumerate(attrs): print(f'  {sum(r[j] for r in inc):4d}  {a}')
