"""2.5.0-alpha3 sounds: T6 Seraphim tier. Original synthesis.
Seraphim = pure tones and deep bass (TZ 2.3); antimatter = bright crackling plasma; singular = implosion + sub-bass.
Every sound keeps a continuous noise bed under its tones: sparse tonal partials crashed the v146 client's
OGG decoder in alpha2 (see t5.py), so run tools/clienttest.sh after changing anything here.
Run: .venv/bin/python tools/sfx/t6.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfxlib import SR, t_, lp, hp, bp, env, sweep, noise, at, metal, crackle, reverb, save  # noqa: E402


def chirp(t, f0, f1, T):
    f = f0 * (f1 / f0) ** np.clip(t / T, 0, 1)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def boom(t, f0=100, f1=26, tau=0.4, nlp=800, g=1.0):
    n = noise(len(t))
    return (sweep(t, f0, f1, 0.07) * env(t, tau) + lp(n, nlp) * env(t, tau * 0.7) * 0.9
            + bp(n, 1200, 5000) * env(t, 0.03) * 0.5) * g


def choir(t, freqs, lfo=0.2, depth=0.3):
    s = np.zeros_like(t)
    for i, f in enumerate(freqs):
        vib = 1 + 0.003 * np.sin(2 * np.pi * (4.5 + 0.3 * i) * t + i)
        s += np.sin(2 * np.pi * np.cumsum(np.full_like(t, f) * vib) / SR) * (1 - depth + depth * np.sin(2 * np.pi * lfo * (i + 1) * t + i))
    return s / len(freqs)


def bed(n, lo=200, hi=3000, g=0.05):
    return bp(noise(n), lo, hi) * g


# --- Requiem salvo: rising choir charge -> three-barrel tonal blast with a deep sub drop
t = t_(3.6)
x = np.zeros_like(t)
c = t_(0.8)
at(x, choir(c, [220, 277, 330, 440, 554]) * (c / 0.8) ** 1.8 * 0.6, 0.0)
at(x, chirp(c, 300, 2400, 0.8) * (c / 0.8) ** 2 * 0.15, 0.0)
at(x, boom(t_(2.8), 90, 20, 0.85, 500, 1.4), 0.75)
at(x, choir(t_(2.4), [110, 165, 220, 330]) * env(t_(2.4), 0.9, 0.01) * 0.5, 0.75)
at(x, lp(crackle(t_(1.6), 140, 0.6), 2800) * 0.3, 0.75)
x += bed(len(t), 300, 4000, 0.03)
save(reverb(x, 0.5, 1.1), 'requiem-shoot')

# --- Requiem impact (quantum and singular): implosion swell -> detonation -> descending sub ring-out
t = t_(3.8)
x = np.zeros_like(t)
s = t_(0.45)
at(x, chirp(s, 3000, 200, 0.45) * (s / 0.45) ** 2 * 0.4, 0.0)
at(x, hp(noise(len(s)), 2500) * (s / 0.45) ** 3 * 0.25, 0.0)
at(x, boom(t_(3.3), 80, 16, 0.9, 380, 1.5), 0.42)
at(x, chirp(t_(3.0), 70, 28, 3.0) * env(t_(3.0), 1.2, 0.02) * 0.8, 0.44)
at(x, choir(t_(2.5), [330, 415, 494]) * env(t_(2.5), 0.8, 0.02) * 0.25, 0.46)
at(x, lp(crackle(t_(2.0), 260, 1.0), 3000) * 0.35, 0.44)
x += bed(len(t), 150, 2500, 0.03)
save(reverb(x, 0.55, 1.15), 'requiem-hit')

# --- Obelisk beam (loop): bright harmonic column, slow shimmer, bass hum
t = t_(2.0)
x = choir(t, [174.6, 261.6, 349.2, 523.3, 698.5], lfo=0.5, depth=0.25) * 0.8
x += np.sin(2 * np.pi * 87.3 * t) * 0.35
x += np.sin(2 * np.pi * 1396.9 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 4 * t)) * 0.10
x += bed(len(t), 2500, 9000, 0.07)
save(x, 'obelisk-beam', loop=True, peak=0.75)

# --- Seraphim Net interception: low sweep + crystalline ping + soft thump
t = t_(1.2)
x = chirp(t, 1800, 260, 0.25) * env(t, 0.12, 0.003) * 0.5
x += choir(t, [988, 1319, 1976]) * env(t, 0.45, 0.004) * 0.45
x += lp(noise(len(t)), 300) * env(t, 0.08) * 0.5
x += bed(len(t), 3000, 9000, 0.04)
save(reverb(x, 0.4, 0.9), 'seraphim-net')

# --- Chronofield hum (loop): slow clock-like pulse under a sustained low chord
t = t_(4.0)
tick = np.zeros_like(t)
for k in range(8):
    at(tick, bp(noise(int(0.02 * SR)), 1500, 5000) * np.exp(-np.arange(int(0.02 * SR)) / (0.004 * SR)), k * 0.5)
x = choir(t, [65.4, 98.0, 130.8, 196.0], lfo=0.25, depth=0.35) * 0.9 + tick * 0.25
x += lp(noise(len(t)), 500) * 0.15
save(lp(x, 2500), 'chrono-hum', loop=True, peak=0.7)

# --- Seraphim Dome hum (loop): wide low choir, breathing
t = t_(4.0)
x = choir(t, [55.0, 82.4, 110.0, 164.8, 220.0, 329.6], lfo=0.25, depth=0.4)
x += lp(noise(len(t)), 350) * 0.2
save(lp(x, 1800), 'dome-hum', loop=True, peak=0.7)

# --- Antimatter loop (trap / refinery): bright plasma crackle over a resonant drone
t = t_(3.0)
x = lp(noise(len(t)), 900) * 0.35
x += hp(crackle(t, 90, 3.0), 2500) * 0.25
x += choir(t, [146.8, 220.0, 293.7], lfo=1 / 3, depth=0.4) * 0.6
save(x, 'antimatter-loop', loop=True, peak=0.7)

# --- Collider loop: rising cyclotron whine (period 1 s) over a sub drone
t = t_(3.0)
ph = np.cumsum(400 + 300 * ((t % 1.0) / 1.0) ** 2) / SR
x = np.sin(2 * np.pi * ph) * 0.25 + np.sin(2 * np.pi * 2 * ph) * 0.1
x += np.sin(2 * np.pi * 41.2 * t) * 0.8 + np.sin(2 * np.pi * 82.4 * t) * 0.3
x += bp(noise(len(t)), 600, 4000) * 0.08
save(x, 'collider-loop', loop=True, peak=0.72)

# --- Annihilation reactor loop: deep throb + high shimmer + plasma hiss
t = t_(4.0)
x = np.sin(2 * np.pi * 32.7 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.5 * t)) * 1.2
x += np.sin(2 * np.pi * 65.4 * t) * 0.5
x += choir(t, [523.3, 784.0, 1046.5], lfo=0.25, depth=0.5) * 0.12
x += lp(noise(len(t)), 250) * 0.3 + bp(noise(len(t)), 3000, 8000) * 0.04
save(x, 'annihilation-loop', loop=True, peak=0.75)

# --- Annihilation reactor detonation: long white flash, huge boom, collapsing choir
t = t_(5.0)
x = boom(t, 70, 14, 1.4, 300, 1.8)
x += lp(crackle(t, 400, 1.6), 3500) * 0.5
x += hp(noise(len(t)), 3000) * env(t, 0.25, 0.002) * 0.4
c = t_(3.5)
at(x, choir(c, [220, 262, 330, 392]) * env(c, 1.2, 0.05) * np.linspace(1, 0.5, len(c)) * 0.35, 0.3)
save(reverb(x, 0.6, 1.2), 'annihilation-blast')
print('T6 sounds written to', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'mod', 'sounds')))
