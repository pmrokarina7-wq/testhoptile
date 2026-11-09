"""2.5.0-alpha2 sounds: T5 Aeon tier + Tempest (UEF Disruptor). Original synthesis.
Aeon = clean tones, glassy shimmer and bass; Tempest = heavy UEF mechanics with a quantum charge.
Run: .venv/bin/python tools/sfx/t5.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfxlib import SR, t_, lp, hp, bp, env, sweep, noise, at, metal, crackle, reverb, save  # noqa: E402

R = np.random.default_rng(505)


def chirp(t, f0, f1, T):
    f = f0 * (f1 / f0) ** np.clip(t / T, 0, 1)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def boom(t, f0=110, f1=34, tau=0.35, nlp=900, g=1.0):
    n = noise(len(t))
    return (sweep(t, f0, f1, 0.06) * env(t, tau) + lp(n, nlp) * env(t, tau * 0.7) * 0.9
            + bp(n, 1200, 5000) * env(t, 0.03) * 0.5) * g


def glass(t, base, n=5, tau=1.2, detune=0.003):
    """Bell-like inharmonic partials with slow beating (Aeon shimmer)."""
    s = np.zeros_like(t)
    for k, m in enumerate((1.0, 2.76, 5.40, 8.93, 13.3)[:n]):
        f = base * m
        s += (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * f * (1 + detune) * t)) * np.exp(-t / (tau / (1 + 0.5 * k))) / (1 + k)
    return s


def pad(t, freqs, lfo=0.25, depth=0.3):
    s = np.zeros_like(t)
    for i, f in enumerate(freqs):
        s += np.sin(2 * np.pi * f * t + i) * (1 - depth + depth * np.sin(2 * np.pi * lfo * (i + 1) * t + i))
    return s / len(freqs)


def loop_t(d):
    # length rounded so the lowest LFOs complete whole cycles
    return t_(d)


# --- Tempest salvo shot: rising quantum capacitor whine -> four-barrel UEF blast with breech clank
t = t_(3.2)
x = np.zeros_like(t)
c = t_(0.6)
at(x, (chirp(c, 220, 1800, 0.6) * 0.4 + chirp(c, 440, 3600, 0.6) * 0.18) * (c / 0.6) ** 1.6, 0.0)
at(x, boom(t_(2.6), 100, 24, 0.75, 600, 1.3), 0.55)
at(x, metal(t_(1.0), [190, 420, 710, 1150], 0.45) * 0.3, 0.55)
at(x, lp(crackle(t_(1.5), 120, 0.6), 2600) * 0.35, 0.55)
at(x, metal(t_(0.4), [1500, 2300, 3300], 0.06) * 0.3, 1.25)
h = t_(0.9)
at(x, bp(noise(len(h)), 2500, 7000) * env(h, 0.35, 0.08) * 0.16, 1.5)
save(reverb(x, 0.45, 1.0), 'tempest-shoot')

# --- Tempest iridium impact: deep detonation + cluster crackle
t = t_(2.8)
x = boom(t, 78, 18, 0.75, 420, 1.4)
x += lp(crackle(t, 320, 1.0), 3200) * 0.45
x += bp(noise(len(t)), 140, 700) * env(t, 1.2, 0.05) * 0.4
save(reverb(x, 0.5, 1.05), 'tempest-hit')

# --- Tempest quantum impact: implosion swell -> detonation -> glassy quantum ring-out
t = t_(3.4)
x = np.zeros_like(t)
s = t_(0.35)
at(x, chirp(s, 2400, 300, 0.35) * (s / 0.35) ** 2 * 0.35, 0.0)
at(x, boom(t_(3.0), 90, 20, 0.6, 500, 1.2), 0.32)
at(x, glass(t_(3.0), 330, tau=1.6) * 0.45, 0.34)
at(x, hp(crackle(t_(1.2), 200, 0.5), 2000) * 0.25, 0.34)
save(reverb(x, 0.55, 1.1), 'tempest-quantum')

# --- Halo beam (loop): sustained harmonic beam with shimmer
t = loop_t(2.0)
x = pad(t, [220, 330, 440, 660, 880], lfo=1.0, depth=0.25) * 0.8
x += np.sin(2 * np.pi * 1760 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * t)) * 0.12
x += bp(noise(len(t)), 3000, 9000) * 0.06
save(x, 'halo-beam', loop=True, peak=0.75)

# --- Quantum interception: short zap + glass ping
t = t_(0.9)
x = chirp(t_(0.12), 4200, 900, 0.12) * env(t_(0.12), 0.05) * 0.6
x = np.concatenate([x, np.zeros(len(t) - len(x))])
x += glass(t, 1250, n=4, tau=0.5) * 0.5
x += hp(noise(len(t)), 4000) * env(t, 0.03) * 0.3
save(reverb(x, 0.35, 0.8), 'quantum-intercept')

# --- Aegis hum (loop): low choir-like chord, slow breathing
t = loop_t(4.0)
x = pad(t, [55, 82.5, 110, 165, 220], lfo=0.25, depth=0.35)
x += np.sin(2 * np.pi * 440 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)) * 0.06
save(lp(x, 1500), 'aegis-hum', loop=True, peak=0.7)

# --- Lumen forge (loop): crystalline resonance over a soft furnace roar.
# Note: an earlier version with sparse detuned bell partials crashed the v146 client's OGG decoder
# (native malloc corruption at load), so this one keeps a continuous broadband bed under the tones.
t = loop_t(3.0)
x = lp(noise(len(t)), 400) * 0.5
x += pad(t, [196, 294, 392, 587], lfo=1 / 3, depth=0.4) * 0.6
x += bp(noise(len(t)), 900, 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * (2 / 3) * t)) * 0.08
x += np.sin(2 * np.pi * 784 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * (1 / 3) * t)) * 0.08
save(x, 'lumen-forge-loop', loop=True, peak=0.7)

# --- Quantum resonator (loop): pulsing resonant tones, 2 Hz throb
t = loop_t(3.0)
throb = 0.55 + 0.45 * np.sin(2 * np.pi * 2 * t) ** 2
x = (np.sin(2 * np.pi * 146.8 * t) + 0.6 * np.sin(2 * np.pi * 293.6 * t) + 0.3 * np.sin(2 * np.pi * 587.3 * t)) * throb
x += np.sin(2 * np.pi * (1174 + 6 * np.sin(2 * np.pi * 1 / 3 * t)) * t) * 0.08
x += bp(noise(len(t)), 800, 3000) * 0.05
save(x, 'resonator-loop', loop=True, peak=0.7)

# --- Quantum generator (loop): deep throbbing bass + high shimmer
t = loop_t(4.0)
x = np.sin(2 * np.pi * 41.2 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 1 * t)) * 1.2
x += np.sin(2 * np.pi * 82.4 * t) * 0.5
x += pad(t, [659, 988, 1319], lfo=0.25, depth=0.5) * 0.12
x += lp(noise(len(t)), 220) * 0.25
save(x, 'qgen-loop', loop=True, peak=0.75)
print('T5 sounds written to', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'mod', 'sounds')))
