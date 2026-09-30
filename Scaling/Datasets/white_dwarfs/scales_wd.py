from fca_check import read_cxt, n_concepts
S = {
 'W1 Spectral features': ['hydrogen lines (A)','helium lines (B)','featureless spectrum (DC)','carbon features (Q)',
     'metal lines (Z, polluted)','magnetic (H or P)','emission lines (e)','peculiar, warm or uncertain type'],
 'W2 Atmosphere and fit': ['hydrogen-dominated atmosphere (fit)','Gaia parameters available','IR-faint (collision-induced absorption)'],
 'W3 Mass (interordinal)': ['Gaia parameters available','mass < 0.45 Msun (low mass)','mass > 0.9 Msun (massive)','mass > 1.1 Msun (ultramassive)'],
 'W4 Temperature (ordinal)': ['Gaia parameters available','Teff > 5000 K','Teff > 10500 K','Teff > 12500 K'],
 'W5 Cooling age (ordinal)': ['Gaia parameters available','cooling age > 0.1 Gyr','cooling age > 1 Gyr','cooling age > 10 Gyr'],
 'W6 Binarity': ['in wide binary or multiple (A6)','wide main-sequence companion','wide white-dwarf companion',
     'wide brown-dwarf companion','wide system with >=3 members','unresolved binary evidence (DD or Gaia orbit)'],
 'W7 Observational': ['within 20 pc','within 10 pc'],
 'X1 Spectral evolution along the cooling sequence': ['hydrogen lines (A)','featureless spectrum (DC)','carbon features (Q)',
     'metal lines (Z, polluted)','hydrogen-dominated atmosphere (fit)','Teff > 5000 K','Teff > 10500 K','Teff > 12500 K'],
 'X2 Binary-evolution and merger signatures': ['mass < 0.45 Msun (low mass)','mass > 0.9 Msun (massive)','mass > 1.1 Msun (ultramassive)',
     'magnetic (H or P)','peculiar, warm or uncertain type','unresolved binary evidence (DD or Gaia orbit)','wide white-dwarf companion'],
}
META = {
 'N1 Intrinsic properties': ['W1 Spectral features','W3 Mass (interordinal)','W4 Temperature (ordinal)','W5 Cooling age (ordinal)','X1 Spectral evolution along the cooling sequence'],
 'N2 Binarity and evolutionary history': ['W6 Binarity','X2 Binary-evolution and merger signatures'],
 'N3 Observation and measurement': ['W2 Atmosphere and fit','W7 Observational'],
}
o,a,r=read_cxt('wd40pc.cxt'); ix={n:i for i,n in enumerate(a)}
out=[f'# Scales for wd40pc.cxt  ({len(o)} objects, {len(a)} attributes, {n_concepts(r, range(len(a)))} concepts)\n']
used=set()
for s,at in S.items():
    used|=set(at); out.append(f'[{s}]  ({n_concepts(r,[ix[x] for x in at])} concepts)'); out+=['  '+x for x in at]; out.append('')
assert used==set(a), set(a)-used
out.append('Meta-groups (scales may recur):')
for m,ss in META.items():
    cols=sorted({ix[x] for s in ss for x in S[s]})
    out.append(f'  {m}: '+'; '.join(ss)+f'   -> {len(cols)} attributes, {n_concepts(r,cols)} concepts')
open('wd40pc_scales.txt','w').write('\n'.join(out)+'\n'); print('\n'.join(out))
