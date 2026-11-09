"""Shared synthesis helpers (from the stage-1 generator). All sounds are original synthesis, no sampled assets."""
import numpy as np, wave, os, subprocess
SR = 44100
OUT = os.environ.get('VG_SOUNDS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mod', 'sounds')); os.makedirs(OUT, exist_ok=True)
R = np.random.default_rng(11)

def t_(d): return np.arange(int(SR*d))/SR
def spec_filter(x, H):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1/SR)
    return np.fft.irfft(X*H(f), len(x))
def lp(x, fc, o=2): return spec_filter(x, lambda f: 1/np.sqrt(1+(f/fc)**(2*o)))
def hp(x, fc, o=2): return spec_filter(x, lambda f: (f/fc)**o/np.sqrt(1+(f/fc)**(2*o)))
def bp(x, lo, hi): return hp(lp(x, hi), lo)
def env(t, tau, a=0.002): return np.minimum(t/a, 1.0)*np.exp(-t/tau)
def sweep(t, f0, f1, tau): return np.sin(2*np.pi*np.cumsum(f1+(f0-f1)*np.exp(-t/tau))/SR)
def noise(n): return R.normal(0, 1, n)
def at(dst, src, sec, g=1.0):
    i = int(sec*SR); n = min(len(src), len(dst)-i)
    if n > 0: dst[i:i+n] += src[:n]*g
def metal(t, fr, tau):
    s = np.zeros_like(t)
    for k, f in enumerate(fr): s += np.sin(2*np.pi*f*t+R.uniform(0, 6))*np.exp(-t/(tau/(1+0.4*k)))/(1+0.6*k)
    return s
def crackle(t, rate, tau):
    s = np.zeros_like(t); n = int(rate*t[-1])
    for c in np.sort(R.uniform(0, t[-1], n)):
        i = int(c*SR); L = int(SR*0.002*R.uniform(0.5, 2))
        if i+L < len(t): s[i:i+L] += noise(L)*np.exp(-np.arange(L)/(L/3))*np.exp(-c/tau)*R.uniform(0.3, 1)
    return s
def reverb(x, mix=0.25, size=0.9):
    y = x.copy()
    for d, g in ((0.031, .5), (0.057, .38), (0.089, .3), (0.13, .22), (0.19, .15), (0.27, .1)):
        i = int(d*size*SR); y[i:] += lp(x, 2500)[:len(x)-i]*g*mix*2
    return y
def save(x, name, loop=False, peak=0.9):
    x = x - x.mean()
    if loop:
        n = int(0.04*SR); fade = np.linspace(0, 1, n)
        x[:n] = x[:n]*fade + x[-n:]*(1-fade); x = x[:-n]
    else:
        n = int(0.01*SR); x[-n:] *= np.linspace(1, 0, n)
    x = np.tanh(1.4*x/np.max(np.abs(x)+1e-9))
    x = x/np.max(np.abs(x))*peak
    w = f'{OUT}/{name}.wav'
    with wave.open(w, 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((x*32767).astype(np.int16).tobytes())
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', w, '-c:a', 'libvorbis', '-q:a', '5', f'{OUT}/{name}.ogg'], check=True)
    os.remove(w)
