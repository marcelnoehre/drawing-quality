def sl(s,a,b): return s[a-1:b].strip()
def fnum(x):
    try: return float(x)
    except: return None
def read_a1(p):
    out=[]
    for l in open(p):
        l=l.rstrip('\n').ljust(368)
        out.append(dict(Name=sl(l,1,22),Gaia=sl(l,24,42),Plx=fnum(sl(l,44,62)),GMAG=fnum(sl(l,137,147)),BPRP=fnum(sl(l,149,161)),
            SpType=sl(l,163,171),Comp=sl(l,173,174),Teff=fnum(sl(l,176,180)),logg=fnum(sl(l,187,192)),Mass=fnum(sl(l,200,205)),
            Teffc=fnum(sl(l,213,217)),Massc=fnum(sl(l,219,223)),Agec=fnum(sl(l,225,229)),ref=sl(l,231,249),Com=sl(l,251,368)))
    return out
def read_a6(p):
    out=[]
    for l in open(p):
        l=l.rstrip('\n').ljust(394)
        out.append(dict(BinType=sl(l,1,8),Id1=sl(l,10,28),Id2=sl(l,30,48),Id3=sl(l,50,68),Name1=sl(l,70,91),Name2=sl(l,93,117),Name3=sl(l,119,135),
            Sp1=sl(l,137,142),Sp2=sl(l,164,171),Sp3=sl(l,193,199),Plx=fnum(sl(l,221,232)),Sep1AU=fnum(sl(l,250,264)),Sep2AU=fnum(sl(l,295,306)),Com=sl(l,321,394)))
    return out
