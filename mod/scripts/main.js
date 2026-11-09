// Vanguard Arsenal 2.0 - stage 1 client scripts. Visual/audio only: safe on servers and in multiplayer.
//  * artillery: ground shadow of the shell (ballistic arc), pulsing impact marker, incoming-shell whistle
//  * shield emitter: hit and break sounds
// Each part disables itself on error; the mod keeps working without scripts.

var ARTY = {
    "vg-howl": { col: Color.valueOf("ffc94a"), whistle: "vg-shell-whistle", h: 10 },
    "vg-scorpion": { col: Color.valueOf("ff3355"), whistle: "scorpion-whistle", h: 16 }
};
var snd = {};
function S(n){
    if(snd[n] === undefined){
        try{ snd[n] = Vars.tree.loadSound(n); }catch(e){ snd[n] = null; }
    }
    return snd[n];
}

var types = null, failA = false, played = {}, clean = 0;
function initTypes(){
    types = new ObjectMap();
    for(var k in ARTY){
        var bl = Vars.content.block(k);
        if(bl == null) continue;
        var seq = bl.ammoTypes.values().toSeq();
        for(var i = 0; i < seq.size; i++) types.put(seq.get(i), ARTY[k]);
    }
}

Events.run(Trigger.draw, function(){
    if(failA) return;
    try{
        if(types == null) initTypes();
        Groups.bullet.each(function(b){
            var cfg = types.get(b.type);
            if(cfg == null) return;
            var s = b.fslope(), h = s * cfg.h, x = b.x, y = b.y;
            Draw.z(Layer.groundUnit - 1);
            Draw.color(0, 0, 0, 0.25 + 0.3 * s);
            Fill.circle(x - h * 0.9, y - h, 1.8 + s * 2.6);

            var rem = b.lifetime - b.time;
            if(rem > 1){
                var v = b.vel;
                var ix = x + v.x * rem, iy = y + v.y * rem;
                var r = Math.max(8, b.type.splashDamageRadius) * (0.4 + 0.6 * b.fout());
                Draw.z(Layer.effect);
                Draw.color(cfg.col, 0.3 + 0.4 * Mathf.absin(Time.time, 3, 1));
                Lines.stroke(1.2);
                Lines.circle(ix, iy, r);
                for(var i = 0; i < 4; i++){
                    var a = i * 90 + 45;
                    Lines.lineAngle(ix + Angles.trnsx(a, r * 0.55), iy + Angles.trnsy(a, r * 0.55), a, r * 0.3);
                }
                Draw.color(cfg.col, 0.7);
                Fill.circle(ix, iy, 1.2);
                if(rem < 70){
                    var id = b.id;
                    if(played[id] === undefined){
                        played[id] = Time.time;
                        var w = S(cfg.whistle);
                        if(w != null) w.at(ix, iy, Mathf.random(0.94, 1.06));
                    }
                }
            }
        });
        Draw.reset();
        if(++clean > 600){
            clean = 0;
            for(var k in played){ if(Time.time - played[k] > 600) delete played[k]; }
        }
    }catch(e){
        failA = true; Draw.reset();
        Log.err("[vg] artillery visuals disabled: " + e);
    }
});

var failB = false, emitter = null, shields = {}, tick = 0;
Events.on(WorldLoadEvent, function(){ shields = {}; });
Events.run(Trigger.update, function(){
    if(failB || Vars.headless || !Vars.state.isGame()) return;
    if(++tick < 4) return;
    tick = 0;
    try{
        if(emitter == null){
            emitter = Vars.content.block("vg-shield-emitter");
            if(emitter == null){ failB = true; return; }
        }
        Groups.build.each(function(b){
            if(b.block != emitter) return;
            var k = b.pos(), p = shields[k], hit = b.hit, br = b.broken;
            if(p !== undefined){
                if(br && !p.br){
                    var s1 = S("shield-break"); if(s1 != null) s1.at(b.x, b.y, 1);
                }else if(!br && hit > p.hit + 0.3){
                    var s2 = S("shield-hit"); if(s2 != null) s2.at(b.x, b.y, Mathf.random(0.9, 1.1), 0.6);
                }
            }
            shields[k] = { hit: hit, br: br };
        });
    }catch(e){
        failB = true;
        Log.err("[vg] shield sounds disabled: " + e);
    }
});

// ===================== Stage 2: BKM cores, engineers, SupCom build rule, ACU death blast, mech steps, spotter marking
// Gameplay parts (build rule, death blast, status) run on the server/host; visuals and sounds run on clients.
var ACU = { "vg-acu-uef": true, "vg-acu-cybran": true };
var BUILDERS = { "vg-acu-uef": true, "vg-acu-cybran": true, "vg-engineer": true };
var VGCORE = { "vg-core-uef": true, "vg-core-cybran": true };
function F(o, n){ var v = o[n]; return (typeof v === "function") ? o[n]() : v; }

// status "spotted" (vg-spotted): marked by a powered spotter beacon, takes +25% damage
var spotted = null;
try{
    spotted = new StatusEffect("spotted");
    spotted.healthMultiplier = 0.8;
    spotted.color = Color.valueOf("6ab8ff");
    spotted.effect = Fx.none;
}catch(e){ spotted = null; Log.err("[vg] spotted status disabled: " + e); }

// engineers start in "assist" mode: they follow and help any construction nearby
Events.on(ContentInitEvent, function(){
    try{
        var eng = Vars.content.unit("vg-engineer");
        if(eng != null) eng.defaultCommand = UnitCommand.assistCommand;
    }catch(e){ Log.err("[vg] engineer default command: " + e); }
});

// SupCom rule: a team that owns a BKM core can only build with ACUs and engineers.
// Checked every frame (before units update) so even instant-cost blocks never start; team scan is cached.
var failC = false, ruleTick = 0, toastAt = -9999, ruleTeams = {}, ruleAny = false;
Events.on(WorldLoadEvent, function(){ ruleTick = 0; ruleTeams = {}; ruleAny = false; });
Events.run(Trigger.update, function(){
    if(failC || !Vars.state.isGame()) return;
    try{
        if(--ruleTick <= 0){
            ruleTick = 30;
            ruleTeams = {}; ruleAny = false;
            var tds = Vars.state.teams.present;
            for(var i = 0; i < tds.size; i++){
                var td = tds.get(i), cs = F(td, "cores");
                for(var j = 0; j < cs.size; j++){
                    if(VGCORE[cs.get(j).block.name]){ ruleTeams[F(td, "team").id] = true; ruleAny = true; break; }
                }
            }
        }
        if(!ruleAny) return;
        var rt = ruleTeams;
        Groups.unit.each(function(u){
            if(!rt[u.team.id] || BUILDERS[u.type.name]) return;
            var q = u.plans;
            if(q == null || q.size == 0) return;
            u.clearBuilding();
            if(!Vars.headless && u == Vars.player.unit() && Time.time - toastAt > 300){
                toastAt = Time.time;
                Vars.ui.showInfoToast(Core.bundle.get("vg.buildrule"), 3);
            }
        });
    }catch(e){
        failC = true;
        Log.err("[vg] build rule disabled: " + e);
    }
});

// ACU death: overload blast hits enemies only (visual + sound come from the unit's deathExplosionEffect/deathSound)
Events.on(UnitDestroyEvent, function(ev){
    try{
        var u = ev.unit;
        if(u == null || !ACU[u.type.name]) return;
        if(!Vars.headless) Effect.shake(7, 70, u.x, u.y);
        if(!Vars.net.client()) Damage.damage(u.team, u.x, u.y, 64, 1200);
    }catch(e){ Log.err("[vg] ACU death blast: " + e); }
});

// heavy mech footsteps: sound + light shake when a foot lands
var failD = false, steps = {}, stepClean = 0;
Events.run(Trigger.update, function(){
    if(failD || Vars.headless || !Vars.state.isGame()) return;
    try{
        Groups.unit.each(function(u){
            if(!ACU[u.type.name] || u.isFlying()) return;
            var q = Math.floor(u.walkExtend(true)), id = u.id, p = steps[id];
            if(p !== undefined && q != p && (q == 1 || q == 3)){
                var sn = S("acu-step");
                if(sn != null) sn.at(u.x, u.y, Mathf.random(0.9, 1.1), 0.7);
                Effect.shake(0.7, 8, u.x, u.y);
            }
            steps[id] = q;
        });
        if(++stepClean > 1800){ stepClean = 0; steps = {}; }
    }catch(e){
        failD = true;
        Log.err("[vg] mech steps disabled: " + e);
    }
});

// spotter beacon: powered beacons mark enemies within 25 tiles (status applied by the server/host)
var failE = false, spotTick = 0, beacon = null, pingAt = {};
Events.on(WorldLoadEvent, function(){ pingAt = {}; steps = {}; });
Events.run(Trigger.update, function(){
    if(failE || spotted == null || !Vars.state.isGame()) return;
    if(++spotTick < 30) return;
    spotTick = 0;
    try{
        if(beacon == null){
            beacon = Vars.content.block("vg-spotter-beacon");
            if(beacon == null){ failE = true; return; }
        }
        Groups.build.each(function(b){
            if(b.block != beacon) return;
            var ef = F(b, "efficiency");
            if(!(ef > 0.01)) return;
            var n = 0, bx = b.x, by = b.y;
            Units.nearbyEnemies(b.team, bx, by, 200, function(u){
                n++;
                if(!Vars.net.client()) u.apply(spotted, 75);
            });
            if(n > 0 && !Vars.headless){
                var k = b.pos(), last = pingAt[k];
                if(last === undefined || Time.time - last > 360){
                    pingAt[k] = Time.time;
                    var ps = S("spot-ping");
                    if(ps != null) ps.at(bx, by, 1, 0.5);
                }
            }
        });
    }catch(e){
        failE = true;
        Log.err("[vg] spotter marking disabled: " + e);
    }
});

// rotating blue target brackets over spotted units
var failF = false;
Events.run(Trigger.draw, function(){
    if(failF || spotted == null) return;
    try{
        Draw.z(Layer.effect + 1);
        Groups.unit.each(function(u){
            if(!u.hasEffect(spotted)) return;
            var r = u.hitSize * 0.75 + 3, x = u.x, y = u.y;
            Draw.color(spotted.color, 0.5 + 0.35 * Mathf.absin(Time.time, 4, 1));
            Lines.stroke(1.1);
            for(var i = 0; i < 4; i++){
                var a = 45 + i * 90 + Time.time * 0.8;
                Lines.lineAngle(x + Angles.trnsx(a, r), y + Angles.trnsy(a, r), a + 180, 3);
            }
        });
        Draw.reset();
    }catch(e){
        failF = true; Draw.reset();
        Log.err("[vg] spotted markers disabled: " + e);
    }
});

// ---------------- Vanguard Arsenal 2.0 - stage 3 scripts
//  * Redoubt / Mantis shells get the same ballistic shadow, impact marker and incoming whistle as Howl / Scorpion
//  * EMP (neodymium magnet) shells: on impact enemy buildings in the blast radius are slowed to 35% for 4 s (server-side only)
//    + blue shock-ring effect for everyone. Units get 'electrified' from the shell itself (JSON status).
ARTY["vg-redoubt"] = { col: Color.valueOf("ffc94a"), whistle: "vg-shell-whistle", h: 12 };
ARTY["vg-mantis"] = { col: Color.valueOf("ff3355"), whistle: "scorpion-whistle", h: 18 };

var empFx = new Effect(42, function(e){
    Draw.color(Color.valueOf("d6f0ff"), Color.valueOf("4aa8ff"), e.fin());
    Lines.stroke(2.6 * e.fout());
    Lines.circle(e.x, e.y, e.rotation * e.finpow());
    Angles.randLenVectors(e.id, 10, e.rotation * e.finpow(), function(x, y){
        Lines.lineAngle(e.x + x, e.y + y, Mathf.angle(x, y), 1 + 5 * e.fout());
    });
    Draw.reset();
});
var empT = null, empFail = false, empSeen = {}, empClean = 0;
function empInit(){
    empT = new ObjectMap();
    var mag = Vars.content.item("vg-magnet");
    var defs = [["vg-mantis", 40], ["vg-hydra", 22]];
    for(var i = 0; i < defs.length; i++){
        var bl = Vars.content.block(defs[i][0]);
        if(bl == null || mag == null) continue;
        var bt = bl.ammoTypes.get(mag);
        if(bt != null) empT.put(bt, defs[i][1]);
    }
}
Events.run(Trigger.update, function(){
    if(empFail || !Vars.state.isPlaying()) return;
    try{
        if(empT == null) empInit();
        if(empT.size == 0) return;
        Groups.bullet.each(function(b){
            var r = empT.get(b.type);
            if(r == null || empSeen[b.id] !== undefined) return;
            if(b.time + Time.delta * 1.5 < b.lifetime) return;
            empSeen[b.id] = Time.time;
            var x = b.x, y = b.y, tm = b.team;
            empFx.at(x, y, r);
            if(Vars.net.client()) return;
            Vars.indexer.eachBlock(null, x, y, r, function(bd){ return bd.team != tm; }, function(bd){
                try{ bd.applySlowdown(0.35, 240); }catch(e2){}
            });
        });
        if(++empClean > 600){ empClean = 0; for(var k in empSeen){ if(Time.time - empSeen[k] > 300) delete empSeen[k]; } }
    }catch(e){ empFail = true; Log.err("[vg] EMP script disabled: " + e); }
});

// ---------------- Vanguard Arsenal 2.5 - T4 scripts
//  * Monolith shells get the ballistic shadow / impact marker / incoming whistle (shared ARTY system)
//  * 'disarmed' status (weapons offline, -40% speed) for Suppressor EMP and Monolith magnet shells
//  * Monolith magnet shell: on impact enemy buildings in 9 tiles are slowed to 30% for 5 s (server-side) + red shock ring
ARTY["vg-monolith"] = { col: Color.valueOf("7fd4ff"), whistle: "scorpion-whistle", h: 26 };

var disarmed = null;
try{
    disarmed = new StatusEffect("disarmed");
    disarmed.disarm = true;
    disarmed.speedMultiplier = 0.6;
    disarmed.color = Color.valueOf("ff3355");
    disarmed.effect = Fx.none;
}catch(e){ Log.err("[vg] disarmed status failed: " + e); }

var dsFx = new Effect(48, function(e){
    Draw.color(Color.white, e.color, e.fin());
    Lines.stroke(3 * e.fout());
    Lines.circle(e.x, e.y, e.rotation * e.finpow());
    Lines.stroke(1.4 * e.fout());
    Lines.circle(e.x, e.y, e.rotation * 0.6 * e.finpow());
    Angles.randLenVectors(e.id, 14, e.rotation * e.finpow(), function(x, y){
        Lines.lineAngle(e.x + x, e.y + y, Mathf.angle(x, y), 1 + 6 * e.fout());
    });
    Draw.reset();
});
var dsT = null, dsFail = false, dsDone = false, dsSeen = {}, dsClean = 0;
// impact effects per bullet type: r = radius (world units), k = building time scale, d = duration (ticks), c = ring colour
var DS_RED = Color.valueOf("ff3355"), DS_GREEN = Color.valueOf("9df0a8");
function dsInit(){
    dsT = new ObjectMap();
    var sup = Vars.content.block("vg-suppressor");
    var mon = Vars.content.block("vg-monolith");
    var tem = Vars.content.block("vg-tempest");
    var mag = Vars.content.item("vg-magnet");
    var qm = Vars.content.item("vg-quantum-matrix");
    if(disarmed != null && sup != null && sup.shootType != null){
        sup.shootType.status = disarmed; sup.shootType.statusDuration = 240;
    }
    if(mon != null && mag != null){
        var bt = mon.ammoTypes.get(mag);
        if(bt != null){
            if(disarmed != null){ bt.status = disarmed; bt.statusDuration = 240; }
            dsT.put(bt, { r: 72, k: 0.3, d: 300, c: DS_RED });
        }
    }
    // Tempest quantum shell: buildings in the blast are frozen for 3 s (units get quantum-stasis from the JSON status)
    if(tem != null && qm != null){
        var qt = tem.ammoTypes.get(qm);
        if(qt != null) dsT.put(qt, { r: 80, k: 0.02, d: 180, c: DS_GREEN });
    }
    dsDone = true;
}
try{ Events.on(ContentInitEvent, function(){ try{ dsInit(); }catch(e){ Log.err("[vg] T4 init: " + e); } }); }catch(e){}
Events.run(Trigger.update, function(){
    if(dsFail || !Vars.state.isPlaying()) return;
    try{
        if(!dsDone) dsInit();
        if(dsT.size == 0) return;
        Groups.bullet.each(function(b){
            var cfg = dsT.get(b.type);
            if(cfg == null || dsSeen[b.id] !== undefined) return;
            if(b.time + Time.delta * 1.5 < b.lifetime) return;
            dsSeen[b.id] = Time.time;
            var x = b.x, y = b.y, tm = b.team;
            dsFx.at(x, y, cfg.r, cfg.c);
            if(Vars.net.client()) return;
            Vars.indexer.eachBlock(null, x, y, cfg.r, function(bd){ return bd.team != tm; }, function(bd){
                try{ bd.applySlowdown(cfg.k, cfg.d); }catch(e2){}
            });
        });
        if(++dsClean > 600){ dsClean = 0; for(var k in dsSeen){ if(Time.time - dsSeen[k] > 300) delete dsSeen[k]; } }
    }catch(e){ dsFail = true; Log.err("[vg] T4 script disabled: " + e); }
});

// ---------------- Vanguard Arsenal 2.5 - T5 scripts
//  * Tempest shells get the ballistic shadow / impact marker / incoming whistle
//  * Quantum Interceptor: every `reload` ticks destroys the nearest enemy shell within range, including the
//    non-hittable T2-T4 artillery shells that vanilla point defence ignores. T5+ shells are immune (TZ rule).
ARTY["vg-tempest"] = { col: Color.valueOf("9df0a8"), whistle: "scorpion-whistle", h: 30 };

var qiFx = new Effect(22, function(e){
    var d = e.data;
    if(d == null) return;
    Draw.color(Color.white, e.color, e.fin());
    Lines.stroke(2.4 * e.fout());
    Lines.line(e.x, e.y, d.x, d.y);
    Lines.stroke(1.2 * e.fout());
    Lines.circle(d.x, d.y, 4 + 14 * e.finpow());
    Fill.circle(e.x, e.y, 3 * e.fout());
    Draw.reset();
});
var qiBlock = null, qiImmune = null, qiFail = false, qiTimers = {}, qiTick = 0;
function qiInit(){
    qiBlock = Vars.content.block("vg-quantum-interceptor");
    qiImmune = new ObjectSet();
    ["vg-tempest"].forEach(function(n){
        var bl = Vars.content.block(n);
        if(bl == null || bl.ammoTypes == null) return;
        bl.ammoTypes.values().toSeq().each(function(bt){
            qiImmune.add(bt);
            if(bt.fragBullet != null) qiImmune.add(bt.fragBullet);
        });
    });
}
Events.on(WorldLoadEvent, function(){ qiTimers = {}; });
Events.run(Trigger.update, function(){
    if(qiFail || !Vars.state.isPlaying() || Vars.net.client()) return;
    try{
        if(qiBlock == null){ qiInit(); if(qiBlock == null){ qiFail = true; return; } }
        Groups.build.each(function(bd){
            if(bd.block != qiBlock) return;
            // efficiency is 0 while vanilla point defence has no hittable target, so use the powered state instead
            var k = bd.pos(), t = (qiTimers[k] || 0) + Time.delta * bd.potentialEfficiency;
            if(t < qiBlock.reload){ qiTimers[k] = t; return; }
            var best = null, bestD = qiBlock.range * qiBlock.range, tm = bd.team, bx = bd.x, by = bd.y;
            Groups.bullet.intersect(bx - qiBlock.range, by - qiBlock.range, qiBlock.range * 2, qiBlock.range * 2, function(b){
                if(b.team == tm || qiImmune.contains(b.type)) return;
                var d2 = (b.x - bx) * (b.x - bx) + (b.y - by) * (b.y - by);
                if(d2 < bestD){ bestD = d2; best = b; }
            });
            if(best == null){ qiTimers[k] = t; return; }
            qiTimers[k] = 0;
            qiFx.at(bx, by, 0, qiBlock.color, new Vec2(best.x, best.y));
            Fx.absorb.at(best.x, best.y, 0, qiBlock.color);
            qiBlock.shootSound.at(bx, by, Mathf.random(0.95, 1.05));
            best.remove();
        });
    }catch(e){ qiFail = true; Log.err("[vg] quantum interceptor disabled: " + e); }
});
