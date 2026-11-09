"""2.5.0-alpha3 sounds: T6 Seraphim tier. Original synthesis.
Seraphim = clean tones, choir-like chords and deep bass; singularity = implosion before the blast.
Every sound keeps a quiet broadband bed under its tones: sparse pure partials crashed the v146 OGG decoder (see t5.py).
Run: .venv/bin/python tools/sfx/t6.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfxlib import SR, t_, lp, hp, bp, env, sweep, noise, at, metal, crackle, reverb, save, OUT  # noqa: E402


def chirp(t, f0, f1, T):
    f = f0 * (f1 / f0) ** np.clip(t / T, 0, 1)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def boom(t, f0=110, f1=30, tau=0.4, nlp=800, g=1.0):
    n = noise(len(t))
    return (sweep(t, f0, f1, 0.07) * env(t, tau) + lp(n, nlp) * env(t, tau * 0.7) * 0.9
            + bp(n, 1200, 5000) * env(t, 0.03) * 0.45) * g


def choir(t, freqs, vib=5.0, depth=0.004, lfo=0.3):
    """Stacked saw-ish voices (3 harmonics), slight vibrato and slow swell: the Seraphim 'chant'."""
    s = np.zeros_like(t)
    for i, f in enumerate(freqs):
        ph = 2 * np.pi * np.cumsum(f * (1 + depth * np.sin(2 * np.pi * (vib + 0.37 * i) * t + i))) / SR
        v = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
        s += v * (0.75 + 0.25 * np.sin(2 * np.pi * lfo * (i + 1) * t + 2 * i))
    return s / len(freqs)


def bed(t, g=0.05, fc=600):
    return lp(noise(len(t)), fc) * g


def glass(t, base, n=4, tau=1.2, detune=0.003):
    s = np.zeros_like(t)
    for k, m in enumerate((1.0, 2.76, 5.40, 8.93)[:n]):
        f = base * m
        s += (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * f * (1 + detune) * t)) * np.exp(-t / (tau / (1 + 0.5 * k))) / (1 + k)
    return s


# --- Requiem salvo: sub-bass charge + rising chant -> three staggered heavy shots, choir tail
t = t_(4.2)
x = bed(t, 0.04)
c = t_(0.9)
at(x, (chirp(c, 36, 110, 0.9) * 0.9 + choir(c, [220, 277, 330]) * 0.35) * (c / 0.9) ** 2, 0.0)
for i in range(3):
    at(x, boom(t_(3.0), 95, 22, 0.8, 520, 1.25 - 0.15 * i), 0.85 + 0.23 * i)
    at(x, metal(t_(0.6), [160, 340, 610, 980], 0.3) * 0.22, 0.86 + 0.23 * i)
at(x, choir(t_(2.6), [110, 165, 220, 277]) * env(t_(2.6), 1.0, 0.15) * 0.35, 1.0)
h = t_(1.2)
at(x, bp(noise(len(h)), 2000, 6000) * env(h, 0.45, 0.1) * 0.14, 1.6)
save(reverb(x, 0.5, 1.15), 'requiem-shoot')

# --- Requiem quantum impact: implosion swell -> blast -> violet glass ring
t = t_(3.6)
x = bed(t, 0.04)
s = t_(0.4)
at(x, chirp(s, 2600, 260, 0.4) * (s / 0.4) ** 2 * 0.35, 0.0)
at(x, boom(t_(3.2), 85, 18, 0.7, 480, 1.3), 0.36)
at(x, glass(t_(3.0), 262, tau=1.7) * 0.42, 0.38)
at(x, hp(crackle(t_(1.4), 220, 0.6), 1800) * 0.25, 0.38)
save(reverb(x, 0.55, 1.15), 'requiem-hit')

# --- Singularity impact: gravity suck (noise + falling tone rising in level) -> enormous sub blast + long rumble
t = t_(4.6)
x = bed(t, 0.05, 400)
s = t_(0.55)
suck = (lp(noise(len(s)), 300 + 2600 * (s / 0.55) ** 2) * 0.8 + chirp(s, 900, 70, 0.55) * 0.5) * (s / 0.55) ** 3
at(x, suck, 0.0)
at(x, boom(t_(4.0), 70, 14, 1.2, 380, 1.6), 0.56)
at(x, np.sin(2 * np.pi * 31 * t_(3.6)) * env(t_(3.6), 1.4, 0.05) * 0.6, 0.56)
at(x, lp(crackle(t_(2.6), 260, 1.2), 2600) * 0.4, 0.58)
at(x, chirp(t_(2.2), 520, 60, 2.2) * env(t_(2.2), 0.9, 0.02) * 0.2, 0.6)
save(reverb(x, 0.6, 1.25), 'singularity-hit')

# --- Requiem incoming shell: descending choir tone + rushing air
t = t_(2.0)
x = (choir(t, [880, 1320]) * 0.25 + chirp(t, 1400, 420, 2.0) * 0.3) * np.minimum(t / 1.2, 1.0) ** 1.5
x += bp(noise(len(t)), 700, 3500) * np.minimum(t / 1.6, 1.0) ** 2 * 0.25
x += bed(t, 0.03)
save(x, 'requiem-whistle', peak=0.8)

# --- Obelisk beam (loop): deep beam chord + high sizzle; all partials complete whole cycles in 2 s
t = t_(2.0)
x = np.sin(2 * np.pi * 55 * t) * 0.9 + np.sin(2 * np.pi * 110 * t) * 0.5 + np.sin(2 * np.pi * 165 * t) * 0.3
x *= 0.75 + 0.25 * np.sin(2 * np.pi * 4 * t)
x += choir(t, [330, 440, 660], vib=4.0, lfo=0.5) * 0.25
x += bp(noise(len(t)), 2500, 8000) * (0.6 + 0.4 * np.sin(2 * np.pi * 8 * t)) * 0.12
x += bed(t, 0.08, 500)
save(x, 'obelisk-beam', loop=True, peak=0.75)

# --- Seraphim Net interception: bright descending zap + bass thump + glass ping
t = t_(1.3)
x = bed(t, 0.03)
z = t_(0.16)
at(x, chirp(z, 5200, 700, 0.16) * env(z, 0.07) * 0.6, 0.0)
at(x, np.sin(2 * np.pi * 60 * t_(0.5)) * env(t_(0.5), 0.15) * 0.8, 0.02)
at(x, glass(t_(1.2), 784, n=3, tau=0.6) * 0.45, 0.03)
at(x, hp(noise(len(t)), 4000) * env(t, 0.03) * 0.3, 0.0)
save(reverb(x, 0.4, 0.9), 'seraph-intercept')

# --- Chronofield (loop): slow detuned pad, soft clock ticks every 0.5 s, reversed swells
t = t_(4.0)
x = choir(t, [98, 147, 196], vib=0.5, depth=0.006, lfo=0.25) * 0.5
for k in range(8):
    tick = bp(noise(int(SR * 0.03)), 1500, 6000) * np.exp(-np.arange(int(SR * 0.03)) / (SR * 0.006))
    at(x, tick * (0.35 if k % 2 == 0 else 0.2), k * 0.5)
sw = np.sin(np.pi * (t % 2.0) / 2.0) ** 4
x += bp(noise(len(t)), 400, 2400) * sw * 0.12
x += bed(t, 0.06, 500)
save(x, 'chrono-field', loop=True, peak=0.7)

# --- Seraphim Dome hum (loop): deep chant chord, slow breathing
t = t_(4.0)
x = choir(t, [55, 82.5, 110, 138.75], vib=0.25, depth=0.003, lfo=0.25)
x += np.sin(2 * np.pi * 440 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)) * 0.05
x += bed(t, 0.08, 400)
save(lp(x, 1600), 'dome-hum', loop=True, peak=0.7)

# --- Antimatter trap (loop): humming containment tone, electric crackle, 1 Hz pulse
t = t_(3.0)
x = np.sin(2 * np.pi * 98 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 1 * t) ** 2) + 0.4 * np.sin(2 * np.pi * 196 * t)
x += hp(crackle(t, 90, 3.0), 1500) * 0.35
x += bp(noise(len(t)), 600, 3500) * 0.08
x += bed(t, 0.08, 400)
save(x, 'antimatter-loop', loop=True, peak=0.7)

# --- Singularity collider (loop): particle ring whirring up once per second + deep throb
t = t_(4.0)
ph = (t % 1.0)
f = 220 + 660 * ph ** 2
x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.3 + 0.7 * ph) * 0.35
x += np.sin(2 * np.pi * 41.25 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 1 * t)) * 0.9
x += bp(noise(len(t)), 900, 5000) * (0.4 + 0.6 * ph) * 0.1
x += bed(t, 0.08, 400)
save(x, 'collider-loop', loop=True, peak=0.72)

# --- Annihilation reactor (loop): sub rumble, 2 Hz throb, high containment whine, crackle
t = t_(4.0)
x = np.sin(2 * np.pi * 33 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 2 * t)) * 1.1 + np.sin(2 * np.pi * 66 * t) * 0.4
x += np.sin(2 * np.pi * (1760 + 8 * np.sin(2 * np.pi * 0.25 * t)) * t) * 0.04
x += lp(crackle(t, 70, 4.0), 3000) * 0.2
x += bed(t, 0.12, 300)
save(x, 'annihilation-loop', loop=True, peak=0.75)

# --- Annihilation reactor destroyed: whine collapse -> colossal blast -> long rolling rumble
t = t_(6.0)
x = bed(t, 0.05, 400)
w = t_(0.5)
at(x, chirp(w, 1760, 120, 0.5) * (1 - w / 0.5) * 0.35, 0.0)
at(x, boom(t_(5.4), 80, 12, 1.6, 360, 1.8), 0.45)
at(x, lp(noise(int(SR * 5.0)), 120) * env(t_(5.0), 1.8, 0.2) * 0.9, 0.5)
at(x, lp(crackle(t_(3.5), 300, 1.4), 3200) * 0.45, 0.47)
at(x, glass(t_(3.0), 196, n=3, tau=1.8) * 0.2, 0.5)
save(reverb(x, 0.6, 1.3), 'annihilation-blast')

print('T6 sounds written to', os.path.abspath(OUT))
