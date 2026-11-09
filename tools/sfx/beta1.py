"""2.5.0-alpha4 sounds: T1-T4 economy and logistics gaps. Original synthesis.
Every sound keeps a continuous noise bed: sparse tonal partials crashed the v146 client's OGG decoder in alpha2
(see t5.py), so run tools/clienttest.sh after changing anything here.
Run: .venv/bin/python tools/sfx/beta1.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfxlib import SR, t_, lp, hp, bp, env, sweep, noise, at, metal, crackle, reverb, save  # noqa: E402

# --- Heat engine (loop, 2 s): steam chuffs at 2 Hz over a firebox roar and a low mechanical thump
t = t_(2.0)
x = lp(noise(len(t)), 350) * 0.45
x += lp(crackle(t, 40, 2.0), 2500) * 0.15
for k in range(4):
    c = t_(0.22)
    at(x, bp(noise(len(c)), 500, 3500) * env(c, 0.07, 0.01) * 0.9, k * 0.5)
    at(x, np.sin(2 * np.pi * 55 * c) * env(c, 0.08, 0.003) * 0.6, k * 0.5)
save(x, 'heat-engine-loop', loop=True, peak=0.7)

# --- Hydrocarbon plant (loop, 3 s): gas turbine whine with a slow beat, combustion roar
t = t_(3.0)
x = np.sin(2 * np.pi * 820 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * (1 / 3) * t)) * 0.18
x += np.sin(2 * np.pi * 1640 * t) * 0.06
x += lp(noise(len(t)), 600) * 0.6 + bp(noise(len(t)), 1500, 6000) * 0.10
x += np.sin(2 * np.pi * 46 * t) * 0.35
save(x, 'hydrocarbon-loop', loop=True, peak=0.7)

# --- Nanite vat (loop, 3 s): bubbling slurry, stirrer hum, faint electronic chatter
t = t_(3.0)
x = lp(noise(len(t)), 300) * 0.35
x += np.sin(2 * np.pi * 98 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 1 * t)) * 0.4
R = np.random.default_rng(7)
for c0 in np.sort(R.uniform(0, 2.9, 24)):
    c = t_(0.06)
    f = R.uniform(250, 700)
    at(x, np.sin(2 * np.pi * np.cumsum(f * (1 + 2.5 * c / 0.06)) / SR) * env(c, 0.02, 0.004) * 0.35, c0)
x += bp(noise(len(t)), 3000, 8000) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)) * 0.04
save(x, 'vat-loop', loop=True, peak=0.68)

# --- Heavy mass driver shot: capacitor whine -> magnetic thunk -> rail ring
t = t_(1.6)
x = np.zeros_like(t)
c = t_(0.35)
at(x, np.sin(2 * np.pi * np.cumsum(400 + 2600 * (c / 0.35) ** 2) / SR) * (c / 0.35) ** 1.5 * 0.35, 0.0)
s = t_(1.2)
at(x, sweep(s, 160, 40, 0.05) * env(s, 0.18) * 1.1 + lp(noise(len(s)), 900) * env(s, 0.10) * 0.7, 0.33)
at(x, metal(t_(1.0), [620, 1310, 2100, 3050], 0.35) * 0.35, 0.34)
x += bp(noise(len(t)), 2000, 7000) * 0.02
save(reverb(x, 0.35, 0.9), 'driver-shoot')
print('beta1 sounds written to', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'mod', 'sounds')))
