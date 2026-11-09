"""2.5.0-beta2 sounds: ACU modules. Original synthesis.
Every sound keeps a continuous noise bed: sparse tonal partials crashed the v146 client's OGG decoder in alpha2
(see t5.py), so run tools/clienttest.sh after changing anything here.
Run: .venv/bin/python tools/sfx/beta2.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfxlib import SR, t_, lp, hp, bp, env, sweep, noise, at, metal, reverb, save  # noqa: E402

# --- Recall Gate (1.6 s): rising charge whine, implosive whoosh, bright shimmer tail at the destination core
t = t_(1.6)
x = bp(noise(len(t)), 300, 4000) * 0.08
c = t_(0.7)
f = 180 + 1400 * (c / 0.7) ** 2
x[:len(c)] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(c / 0.6, 1) * 0.35
x[:len(c)] += bp(noise(len(c)), 1200, 7000) * (c / 0.7) ** 3 * 0.5
w = t_(0.5)
at(x, lp(noise(len(w)), 900) * env(w, 0.12, 0.005) * 1.1, 0.68)
at(x, sweep(w, 260, 55, 0.08) * env(w, 0.18, 0.004) * 0.9, 0.68)
s = t_(0.85)
sh = sum(np.sin(2 * np.pi * fr * s + k) for k, fr in enumerate((1320, 1760, 2215, 2640))) / 4
at(x, (sh * 0.35 + bp(noise(len(s)), 4000, 9000) * 0.25) * (1 - np.exp(-s / 0.02)) * np.exp(-s / 0.3), 0.72)
save(reverb(x, 0.3, 1.1), 'acu-teleport', peak=0.8)

# --- Module install (0.9 s): heavy latch clunk, servo whirr, two-tone confirm
t = t_(0.9)
x = lp(noise(len(t)), 2000) * 0.05
k = t_(0.25)
at(x, metal(k, (190, 410, 760, 1230), 0.06) * 0.8 + lp(noise(len(k)), 600) * env(k, 0.03, 0.002) * 0.9, 0.0)
v = t_(0.35)
at(x, np.sin(2 * np.pi * np.cumsum(420 + 260 * np.sin(np.pi * v / 0.35)) / SR) * np.sin(np.pi * v / 0.35) * 0.22
   + bp(noise(len(v)), 800, 2500) * np.sin(np.pi * v / 0.35) * 0.15, 0.12)
for i, fr in enumerate((880, 1320)):
    b = t_(0.18)
    at(x, (np.sin(2 * np.pi * fr * b) * 0.3 + bp(noise(len(b)), fr * 0.8, fr * 1.3) * 0.08) * env(b, 0.07, 0.003), 0.5 + i * 0.12)
save(reverb(x, 0.2, 0.8), 'acu-module', peak=0.8)
