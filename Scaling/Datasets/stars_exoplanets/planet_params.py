import csv, json
R={r['pl_name'].lower():r for r in csv.DictReader(open('data/PSCompPars_2026.csv'))}
R_old={r['pl_name'].lower():r for r in csv.DictReader(open('data/pscomppars.csv'))}
oec={p['name']:p for p in json.load(open('planets_oec.json'))}
NASA_ALIAS={'HD 95735 b':'GJ 411 b','GJ 229 A b':'GJ 229 b','BD+01 2447 b':'GJ 393 b','BD+11 2576 b':'GJ 514 b',
 'BD+61 195 b':'Gl 49 b','GJ 686 b':'Gl 686 b','HD 102365 A b':'HD 102365 b'}
MJ=317.828
# manual literature values for planets absent from both NASA (2026) and OEC:
MANUAL={'GJ 752 A b': dict(mass_e=12.2, msini=True, P=105.915, a=0.3357, teff=3558, rad=0.47,
                          src='Kaminski et al. 2018, A&A 618, A115 (m sin i, P, a); host Teff/R from same paper'),
        'GJ 3512 c': dict(mass_e=0.20*MJ, msini=True, P=1599.6, a=1.292, teff=3081, rad=0.1636,
                          src='Lopez-Santiago et al. 2020, A&A 641, L1 (m sin i, P, a); host from Morales et al. 2019')}
def num(x):
    try: return float(x)
    except: return None
out=[]
for name,o in oec.items():
    d=dict(name=name, host=o['host'])
    k=NASA_ALIAS.get(name,name).lower()
    n=R.get(k)
    d['in_nasa_2026']= n is not None
    d['in_nasa_older']= k in R_old
    if n:
        d.update(mass_e=num(n['pl_bmasse']), mass_prov=n['pl_bmassprov'], P=num(n['pl_orbper']), a=num(n['pl_orbsmax']),
                 ecc=num(n['pl_orbeccen']), insol=num(n['pl_insol']), teff=num(n['st_teff']), rad=num(n['st_rad']),
                 method=n['discoverymethod'], year=n['disc_year'], controv=n['pl_controv_flag'], src='NASA Exoplanet Archive PSCompPars (2026 mirror)')
    elif o.get('oec'):
        d.update(mass_e=(o['mass']*MJ if o['mass'] else None), mass_prov=('Msini(OEC)' if o.get('inclination') in (None,) else 'Mass(OEC)'),
                 P=o['period'], a=o['semimajoraxis'], ecc=o['eccentricity'], insol=None, teff=o['star_temperature'], rad=o['star_radius'],
                 method=o['discoverymethod'], year=o['discoveryyear'], controv=None, src='Open Exoplanet Catalogue')
    else:
        m=MANUAL[name]; d.update(mass_e=m['mass_e'], mass_prov='Msini(lit)', P=m['P'], a=m['a'], ecc=None, insol=None,
                 teff=m['teff'], rad=m['rad'], method='Radial Velocity', year=None, controv=None, src=m['src'])
    # gap-filling for host parameters: NASA sibling planet of same host, then OEC, then literature
    if d.get('rad') is None or d.get('teff') is None:
        sib=[n for k,n in R.items() if o['host'] and any(NASA_ALIAS.get(x,x).lower()==k for x in oec if oec[x]['host']==o['host'] and x!=name)]
        for n in sib:
            if d.get('teff') is None and num(n['st_teff']): d['teff']=num(n['st_teff'])
            if d.get('rad') is None and num(n['st_rad']): d['rad']=num(n['st_rad'])
    if name=='HD 102365 A b' and d.get('rad') is None:
        d['rad']=0.96; d['src']+='; host radius 0.96 Rsun adopted (classification insensitive: S>>HZ inner edge for any R>0.4)'
    # OEC gap-filling for host parameters
    if d.get('teff') is None and o.get('star_temperature'): d['teff']=o['star_temperature']
    if d.get('rad') is None and o.get('star_radius'): d['rad']=o['star_radius']
    d['transiting']= bool(o.get('istransiting')==1.0 and o.get('radius'))
    if d.get('insol') is None and d.get('teff') and d.get('rad') and d.get('a'):
        d['insol']=(d['rad']**2*(d['teff']/5772)**4)/d['a']**2; d['insol_src']='computed R*^2 Teff^4 / a^2'
    out.append(d)
json.dump(out,open('planet_params.json','w'),indent=1)
for d in out:
    print(f"{d['name']:<20}{str(d['in_nasa_2026'])[0]}{str(d['in_nasa_older'])[0]} M={d['mass_e'] and round(d['mass_e'],2)!s:<8}{str(d['mass_prov']):<12}P={d['P']!s:<11}a={d['a']!s:<9}S={d['insol'] and round(d['insol'],3)!s:<8}T={d['teff']!s:<7}R*={d['rad']!s:<7}{str(d['method'])[:10]:<11}tr={d['transiting']:d} c={d.get('controv')}")
