import numpy as np
from geom import clean

MATS = ['hull_dark','hull_mid','hull_light','red_armor','metal','metal_light','cable','vent','bore','coil','heat','glow','ground',
        'yellow','glass','copper','flame','ore_fer','ore_salt','steel','charge','rglow','team','cy_dark','cy_mid',
        'alu','cobalt','tung','magnet','ore_baux','ore_cob','ore_wolf','ore_neo','chlor','pglow','gglow']
MID = {m: i for i, m in enumerate(MATS)}

class Model:
    def __init__(self):
        self.parts = {}
    def add(self, g, T, m):
        T = clean(T)
        if len(T): self.parts.setdefault(g, []).append((T, m))
    def arrays(self, groups, xforms=None):
        tris, mats, grp = [], [], []
        for g in groups:
            for T, m in self.parts.get(g, []):
                TT = T if not xforms or g not in xforms else xforms[g](T)
                tris.append(TT); mats += [MID[m]]*len(TT); grp += [g]*len(TT)
        return np.concatenate(tris), np.array(mats), np.array(grp)
    def ntri(self):
        return sum(len(T) for v in self.parts.values() for T, _ in v)
