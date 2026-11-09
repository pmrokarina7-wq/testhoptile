"""Generator for the 2.5.0-beta1 content JSON (ACU Mk II-III, engineers T2-T3, command cores, bay plans).
Derived from the Mk I / T1 definitions so stats stay in proportion. Run from the repo root: python3 tools/gen/beta1_content.py (idempotent)."""
import json
import os

C = 'mod/content'


def load(p):
    with open(os.path.join(C, p), encoding='utf-8') as f:
        return json.load(f)


def dump(p, d):
    with open(os.path.join(C, p), 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write('\n')


def acu(src, dst, mk, health, armor, hit, build, mine, cap, speed, res):
    s, dmg = (1.15, 1.8) if mk == 2 else (1.30, 3.0)
    u = load(f'units/{src}.json')
    u.update(health=health, armor=armor, hitSize=hit, buildSpeed=build, mineTier=mine, itemCapacity=cap, speed=speed, research=res)
    u['mechStride'] = round(u['mechStride'] * s, 2)
    u['buildBeamOffset'] = round(u['buildBeamOffset'] * s, 2)
    for w in u['weapons']:
        w['name'] = w['name'].replace(src + '-', f'{dst}-')
        w['x'] = round(w['x'] * s, 2)
        w['y'] = round(w['y'] * s, 2)
        if 'shootY' in w:
            w['shootY'] = round(w['shootY'] * s, 2)
        b = w['bullet']
        for k in ('damage', 'splashDamage', 'lightningDamage'):
            if k in b:
                b[k] = round(b[k] * dmg, 1)
    dump(f'units/{dst}.json', u)
    return u


acu('acu-uef', 'acu-uef-mk2', 2, 3200, 9, 16, 2.4, 4, 120, 0.5, 'vg-core-uef-2')
acu('acu-uef', 'acu-uef-mk3', 3, 7000, 13, 19, 3.4, 5, 180, 0.48, 'vg-core-uef-3')
acu('acu-cybran', 'acu-cybran-mk2', 2, 2800, 7, 15, 2.6, 4, 110, 0.6, 'vg-core-cybran-2')
acu('acu-cybran', 'acu-cybran-mk3', 3, 6000, 11, 18, 3.8, 5, 160, 0.58, 'vg-core-cybran-3')

for t, health, armor, hit, speed, build, mine, cap, es, eo, bo, res in (
        (2, 600, 3, 10, 2.4, 1.5, 3, 60, 1.9, 7.2, 4.1, 'vg-engineer'),
        (3, 1200, 5, 11.5, 2.6, 2.3, 4, 90, 2.2, 8.4, 4.8, 'vg-engineer-2')):
    e = load('units/engineer.json')
    e.update(health=health, armor=armor, hitSize=hit, speed=speed, buildSpeed=build, mineTier=mine, itemCapacity=cap,
             engineSize=es, engineOffset=eo, buildBeamOffset=bo, research=res)
    dump(f'units/engineer-{t}.json', e)

for src, dst, size, health, armor, cap, unitcap, unit, res, req in (
        ('core-uef', 'core-uef-2', 5, 9000, 8, 13000, 24, 'vg-acu-uef-mk2', 'vg-core-uef',
         ['copper/6000', 'lead/6000', 'silicon/4000', 'titanium/2000', 'steel/1500', 'tungsten-core/800', 'magnet/400']),
        ('core-uef', 'core-uef-3', 6, 18000, 12, 20000, 32, 'vg-acu-uef-mk3', 'vg-core-uef-2',
         ['copper/10000', 'lead/10000', 'silicon/7000', 'titanium/4000', 'plastanium/1500', 'superconductor/1000', 'lumen-core/600']),
        ('core-cybran', 'core-cybran-2', 5, 8000, 7, 13000, 26, 'vg-acu-cybran-mk2', 'vg-core-cybran',
         ['copper/6000', 'lead/5000', 'silicon/3500', 'graphite/2000', 'steel/1500', 'tungsten-core/800', 'magnet/400']),
        ('core-cybran', 'core-cybran-3', 6, 16000, 11, 20000, 34, 'vg-acu-cybran-mk3', 'vg-core-cybran-2',
         ['copper/10000', 'lead/9000', 'silicon/6500', 'graphite/3000', 'plastanium/1500', 'superconductor/1000', 'lumen-core/600'])):
    c = load(f'blocks/{src}.json')
    c.update(size=size, health=health, armor=armor, itemCapacity=cap, unitCapModifier=unitcap, unitType=unit, research=res, requirements=req)
    dump(f'blocks/{dst}.json', c)

bay = load('blocks/engineering-bay.json')
names = [p['unit'] for p in bay['plans']]
for unit, time, req in (('vg-engineer-2', 2400, ['silicon/80', 'titanium/40', 'cobalt-alloy/30']),
                        ('vg-engineer-3', 3600, ['silicon/150', 'plastanium/40', 'magnet/40'])):
    if unit not in names:
        bay['plans'].append({'unit': unit, 'time': time, 'requirements': req})
dump('blocks/engineering-bay.json', bay)
print('ok')
