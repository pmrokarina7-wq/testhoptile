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

// ---------------- shared infrastructure (2.5.0-beta1)
//  * settings: vg-supcom (SupCom build rules), vg-shellfx (artillery shadows/markers/whistles), vg-profile (perf log)
//  * building registry: per-frame handlers iterate only the buildings of their own block. The list is rebuilt when
//    a tracked block appears (at most every 10 frames) plus a slow safety refresh, instead of every handler scanning all
//    buildings every frame. Stale entries are skipped with isValid().
//  * R(trigger, name, fn): Events.run with optional per-handler timing (setting vg-profile), logged every 600 frames
function setting(n, def){ try{ return Core.settings.getBool(n, def); }catch(e){ return def; } }
var SET = { supcom: true, shellfx: true, profile: false };
function refreshSettings(){ SET.supcom = setting("vg-supcom", true); SET.shellfx = setting("vg-shellfx", true); SET.profile = setting("vg-profile", false); }
refreshSettings();

var PERF = { t: {}, frames: 0, start: -1 };
// Rhino's toFixed() here keeps one significant digit (142.3 -> "100.0"), so round by hand
function r1(x){ return Math.round(x * 10) / 10; }
function R(trigger, name, fn){
    Events.run(trigger, function(){
        if(!SET.profile){ fn(); return; }
        var t0 = Time.nanos();
        fn();
        PERF.t[name] = (PERF.t[name] || 0) + (Time.nanos() - t0);
    });
}

var REG = { names: {}, byId: null, lists: {}, dirty: true, wait: 0, safety: 0, setTick: 0 };
function track(n){ REG.names[n] = true; REG.byId = null; REG.dirty = true; }
function blds(n){ return REG.lists[n] || []; }
function regRebuild(){
    REG.dirty = false; REG.wait = 10; REG.safety = 120;
    if(REG.byId == null){
        REG.byId = {};
        for(var n in REG.names){ var b = Vars.content.block(n); if(b != null) REG.byId[b.id] = n; }
    }
    var L = {}, by = REG.byId;
    for(var m in REG.names) L[m] = [];
    Groups.build.each(function(b){ var k = by[b.block.id]; if(k !== undefined) L[k].push(b); });
    REG.lists = L;
}
Events.on(WorldLoadEvent, function(){ REG.dirty = true; REG.wait = 0; });
// only a tracked block appearing needs a rebuild; removed buildings fail isValid() until the safety refresh drops them
Events.on(TileChangeEvent, function(ev){
    if(REG.byId == null || (ev.tile != null && REG.byId[ev.tile.block().id] !== undefined)) REG.dirty = true;
});
R(Trigger.update, "registry", function(){
    if(--REG.setTick <= 0){ REG.setTick = 120; refreshSettings(); }
    --REG.wait;
    if((REG.dirty && REG.wait <= 0) || --REG.safety <= 0) regRebuild();
    if(SET.profile){
        if(PERF.start < 0) PERF.start = Time.time;
        // report every 5 s of game time (frame count would depend on the frame rate)
        if(++PERF.frames >= 30 && Time.time - PERF.start >= 300){
            var tot = 0, parts = [];
            for(var k in PERF.t){ var us = PERF.t[k] / 1000 / PERF.frames; tot += us; parts.push(k + " " + r1(us)); }
            Log.info("[vg] perf us/frame total " + r1(tot) + " over " + PERF.frames + " frames | " + parts.join(", ") + " | buildings " + Groups.build.size() + " bullets " + Groups.bullet.size() + " units " + Groups.unit.size());
            PERF.t = {}; PERF.frames = 0; PERF.start = Time.time;
        }
    }
});
function inView(x, y, m){
    var c = Core.camera;
    return Math.abs(x - c.position.x) < c.width / 2 + m && Math.abs(y - c.position.y) < c.height / 2 + m;
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

R(Trigger.draw, "arty", function(){
    if(failA || !SET.shellfx) return;
    try{
        if(types == null) initTypes();
        Groups.bullet.each(function(b){
            var cfg = types.get(b.type);
            if(cfg == null) return;
            var s = b.fslope(), h = s * cfg.h, x = b.x, y = b.y;
            if(inView(x, y, 32)){
                Draw.z(Layer.groundUnit - 1);
                Draw.color(0, 0, 0, 0.25 + 0.3 * s);
                Fill.circle(x - h * 0.9, y - h, 1.8 + s * 2.6);
            }

            var rem = b.lifetime - b.time;
            if(rem > 1){
                var v = b.vel;
                var ix = x + v.x * rem, iy = y + v.y * rem;
                var r = Math.max(8, b.type.splashDamageRadius) * (0.4 + 0.6 * b.fout());
                if(inView(ix, iy, r + 8)){
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
                }
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
track("vg-shield-emitter");
Events.on(WorldLoadEvent, function(){ shields = {}; });
R(Trigger.update, "shieldSounds", function(){
    if(failB || Vars.headless || !Vars.state.isGame()) return;
    if(++tick < 4) return;
    tick = 0;
    try{
        var list = blds("vg-shield-emitter");
        for(var i = 0; i < list.length; i++){
            var b = list[i];
            if(!b.isValid()) continue;
            var k = b.pos(), p = shields[k], hit = b.hit, br = b.broken;
            if(p !== undefined){
                if(br && !p.br){
                    var s1 = S("shield-break"); if(s1 != null) s1.at(b.x, b.y, 1);
                }else if(!br && hit > p.hit + 0.3){
                    var s2 = S("shield-hit"); if(s2 != null) s2.at(b.x, b.y, Mathf.random(0.9, 1.1), 0.6);
                }
            }
            shields[k] = { hit: hit, br: br };
        }
    }catch(e){
        failB = true;
        Log.err("[vg] shield sounds disabled: " + e);
    }
});

// ===================== Stage 2: BKM cores, engineers, SupCom build rule, ACU death blast, mech steps, spotter marking
// Gameplay parts (build rule, death blast, status) run on the server/host; visuals and sounds run on clients.
// ACU marks: mk (core tier), blast radius (world units) and damage of the overload blast on death.
var ACU_MK = {
    "vg-acu-uef": { mk: 1, r: 64, dmg: 1200 }, "vg-acu-uef-mk2": { mk: 2, r: 80, dmg: 2000 }, "vg-acu-uef-mk3": { mk: 3, r: 96, dmg: 3000 },
    "vg-acu-cybran": { mk: 1, r: 64, dmg: 1200 }, "vg-acu-cybran-mk2": { mk: 2, r: 80, dmg: 2000 }, "vg-acu-cybran-mk3": { mk: 3, r: 96, dmg: 3000 }
};
var ACU = {};
for(var acuName in ACU_MK) ACU[acuName] = true;
// engineers: the highest block tier each one may build (TZ: T1 up to T2, T2 up to T4, T3 everything)
var ENG_MAX = { "vg-engineer": 2, "vg-engineer-2": 4, "vg-engineer-3": 6 };
var BUILDERS = {};
for(var bn in ACU) BUILDERS[bn] = true;
for(var en in ENG_MAX) BUILDERS[en] = true;
var VGCORE = { "vg-core-uef": true, "vg-core-cybran": true, "vg-core-uef-2": true, "vg-core-cybran-2": true, "vg-core-uef-3": true, "vg-core-cybran-3": true };
var BAN_TICKS = 1800;
function F(o, n){ var v = o[n]; return (typeof v === "function") ? o[n]() : v; }

// block tier = highest tier among its build costs (vanilla items mapped onto the mod's tiers)
var ITEM_TIER = {
    "copper": 1, "lead": 1, "sand": 1, "coal": 1, "scrap": 1, "graphite": 1, "metaglass": 1, "silicon": 1, "spore-pod": 1,
    "titanium": 2, "thorium": 2, "plastanium": 3, "phase-fabric": 3, "surge-alloy": 4,
    "vg-steel": 1, "vg-charge": 1, "vg-ferrolite": 1, "vg-saltpeter": 1,
    "vg-aluminum": 2, "vg-cobalt-alloy": 2, "vg-bauxite": 2, "vg-cobaltite": 2,
    "vg-tungsten-core": 3, "vg-magnet": 3, "vg-wolframite": 3, "vg-neodymite": 3,
    "vg-iridium": 4, "vg-superconductor": 4, "vg-iridite": 4, "vg-tritium-ice": 4,
    "vg-lumen-core": 5, "vg-quantum-matrix": 5, "vg-luminite": 5, "vg-null-quartz": 5,
    "vg-seraphimium": 6, "vg-singular-core": 6, "vg-seraphite": 6, "vg-singularite": 6
};
var tierCache = {};
function blockTier(b){
    var t = tierCache[b.id];
    if(t !== undefined) return t;
    t = 1;
    var req = b.requirements;
    for(var i = 0; i < req.length; i++){ var it = ITEM_TIER[req[i].item.name]; if(it !== undefined && it > t) t = it; }
    tierCache[b.id] = t;
    return t;
}

// status "spotted" (vg-spotted): marked by a powered spotter beacon, takes +25% damage
var spotted = null;
try{
    spotted = new StatusEffect("spotted");
    spotted.healthMultiplier = 0.8;
    spotted.color = Color.valueOf("6ab8ff");
    spotted.effect = Fx.none;
}catch(e){ spotted = null; Log.err("[vg] spotted status disabled: " + e); }

// hidden status "supcom-nobuild": buildSpeedMultiplier 0 makes canBuild() false, so the unit cannot build at all,
// including plans its AI copies inside the unit update (BuilderAI assist), after the plan check below has run
var noBuild = null;
try{
    noBuild = new StatusEffect("supcom-nobuild");
    noBuild.buildSpeedMultiplier = 0;
    noBuild.show = false;
    noBuild.effect = Fx.none;
}catch(e){ noBuild = null; Log.err("[vg] no-build status disabled: " + e); }

// ACU modules (2.5.0-beta2): two of six at a time, bought at an own core (12 tiles) with core items.
// Each module is a hidden permanent status, so it is synced to clients and saved with the unit for free; the slot
// count reads getDuration() (exact within a frame, unlike hasEffect which updates with the unit). Periodic effects
// (shield, repair, missiles) run in the "acuMods" handler below; cannon and build are plain status multipliers.
var MOD_DEFS = [
    { id: "cannon", cost: [["graphite", 400], ["vg-steel", 250], ["silicon", 150]], set: { damageMultiplier: 1.35 } },
    { id: "shield", cost: [["silicon", 350], ["titanium", 200], ["vg-aluminum", 100]] },
    { id: "build", cost: [["silicon", 300], ["vg-steel", 200], ["lead", 300]], set: { buildSpeedMultiplier: 1.75 } },
    { id: "repair", cost: [["silicon", 300], ["vg-aluminum", 150], ["graphite", 200]] },
    { id: "missiles", cost: [["graphite", 300], ["vg-charge", 250], ["titanium", 150]] },
    { id: "teleport", cost: [["silicon", 500], ["vg-cobalt-alloy", 150], ["titanium", 250]] }
];
var MOD = {}, MOD_SLOTS = 2, MOD_FOREVER = 1e9, MOD_CORE_RANGE = 12 * 8, TP_COOLDOWN = 7200;
var tpCool = null, assembly = null;
try{
    MOD_DEFS.forEach(function(d){
        var st = new StatusEffect("acu-mod-" + d.id);
        st.permanent = true;
        st.show = false;
        st.effect = Fx.none;
        if(d.set) for(var k in d.set) st[k] = d.set[k];
        d.st = st;
        MOD[d.id] = d;
    });
    tpCool = new StatusEffect("acu-tp-cooldown");
    tpCool.color = Color.valueOf("8fb8ff");
    tpCool.effect = Fx.none;
    // respawn in the core after an ACU loss: the new ACU stands assembled in the core for the rest of the 30 s ban
    // (vanilla respawn delay is a final constant, so the wait is a status: synced, saved, shown with a timer)
    assembly = new StatusEffect("acu-assembly");
    assembly.speedMultiplier = 0;
    assembly.reloadMultiplier = 0;
    assembly.buildSpeedMultiplier = 0;
    assembly.healthMultiplier = 10;
    assembly.disarm = true;
    assembly.color = Color.valueOf("ffd37f");
    assembly.effect = Fx.none;
}catch(e){ MOD_DEFS = []; MOD = {}; Log.err("[vg] ACU modules disabled: " + e); }

// engineers start in "assist" mode: they follow and help any construction nearby
Events.on(ContentInitEvent, function(){
    try{
        for(var n in ENG_MAX){
            var eng = Vars.content.unit(n);
            if(eng != null) eng.defaultCommand = UnitCommand.assistCommand;
        }
    }catch(e){ Log.err("[vg] engineer default command: " + e); }
});

// SupCom rules (setting vg-supcom, on by default):
//  * a team that owns a BKM core can only build with ACUs and engineers;
//  * after an ACU dies its team cannot build for 30 s;
//  * engineers only build up to their tier (T1 <= T2 blocks, T2 <= T4, T3 everything).
// Checked every frame before units update, so even instant-cost blocks never start; team scan is cached.
var failC = false, ruleTick = 0, toastAt = -9999, ruleTeams = {}, ruleAny = false, engAny = false, banUntil = {};
Events.on(WorldLoadEvent, function(){ ruleTick = 0; ruleTeams = {}; ruleAny = false; engAny = false; banUntil = {}; });
function ruleToast(u, key){
    if(!Vars.headless && u == Vars.player.unit() && Time.time - toastAt > 300){
        toastAt = Time.time;
        Vars.ui.showInfoToast(Core.bundle.get(key), 3);
    }
}
R(Trigger.update, "buildRule", function(){
    if(failC || !SET.supcom || !Vars.state.isGame()) return;
    try{
        // game-time timers (Time.delta), not frame counts: at low FPS a frame is up to 6 ticks and the statuses below
        // (45 ticks here, spotted 75, chrono 40) would lapse between passes
        if((ruleTick -= Time.delta) <= 0){
            ruleTick = 30;
            ruleTeams = {}; ruleAny = false; engAny = false;
            var tds = Vars.state.teams.present;
            for(var i = 0; i < tds.size; i++){
                var td = tds.get(i), cs = F(td, "cores");
                for(var j = 0; j < cs.size; j++){
                    if(VGCORE[cs.get(j).block.name]){ ruleTeams[F(td, "team").id] = true; ruleAny = true; break; }
                }
            }
            var now0 = Time.time, nb = (noBuild != null && !Vars.net.client()) ? noBuild : null;
            Groups.unit.each(function(u){
                var tn = u.type.name;
                if(ENG_MAX[tn] !== undefined) engAny = true;
                if(nb == null || !(u.type.buildSpeed > 0)) return;
                var ban = banUntil[u.team.id];
                // the status outlives this 30-tick pass, so units stay blocked between passes
                if(ban !== undefined && ban > now0) u.apply(nb, Math.min(45, ban - now0));
                else if(ruleTeams[u.team.id] && !BUILDERS[tn]) u.apply(nb, 45);
            });
        }
        var now = Time.time, banAny = false;
        for(var k in banUntil){ if(banUntil[k] > now) banAny = true; else delete banUntil[k]; }
        if(!ruleAny && !engAny && !banAny) return;
        var rt = ruleTeams;
        Groups.unit.each(function(u){
            var q = u.plans;
            if(q == null || q.size == 0) return;
            var tn = u.type.name;
            if(banAny && banUntil[u.team.id] > now){ u.clearBuilding(); ruleToast(u, "vg.buildban"); return; }
            if(rt[u.team.id] && !BUILDERS[tn]){ u.clearBuilding(); ruleToast(u, "vg.buildrule"); return; }
            var max = ENG_MAX[tn];
            if(max === undefined) return;
            for(var i = q.size - 1; i >= 0; i--){
                var p = q.get(i);
                if(!p.breaking && p.block != null && blockTier(p.block) > max){ q.removeIndex(i); ruleToast(u, "vg.engtier"); }
            }
        });
    }catch(e){
        failC = true;
        Log.err("[vg] build rule disabled: " + e);
    }
});

// ACU death: overload blast hits enemies only (visual + sound come from the unit's deathExplosionEffect/deathSound);
// stronger for higher marks. With SupCom rules on, the team cannot build for 30 s afterwards.
Events.on(UnitDestroyEvent, function(ev){
    try{
        var u = ev.unit, m = (u == null) ? undefined : ACU_MK[u.type.name];
        if(m === undefined) return;
        if(!Vars.headless) Effect.shake(5 + 2 * m.mk, 70, u.x, u.y);
        if(!Vars.net.client()) Damage.damage(u.team, u.x, u.y, m.r, m.dmg);
        if(SET.supcom){
            banUntil[u.team.id] = Time.time + BAN_TICKS; ruleTick = 0;
            // ACUs alive at the moment of the loss keep fighting; only ACUs the core spawns afterwards are assembled
            var known = {}, tm = u.team;
            Groups.unit.each(function(o){ if(o != u && o.team == tm && ACU[o.type.name]) known[o.id] = true; });
            banKnown[tm.id] = known;
        }
        // "Veteran" setting: losing the ACU you pilot loses the game (PvP: the team's cores fall)
        if(!Vars.net.client() && setting("vg-acu-defeat", false) && u.isPlayer()){
            if(Vars.state.rules.pvp) u.team.cores().copy().each(function(c){ c.kill(); });
            else Call.gameOver(Vars.state.rules.waveTeam);
        }
    }catch(e){ Log.err("[vg] ACU death blast: " + e); }
});

// core upgrade (Command Center / Citadel core placed over a smaller BKM core): players piloting a lower-mark ACU
// spawned by a core get the new mark in place, keeping their health fraction, modules and timers
Events.on(BlockBuildEndEvent, function(ev){
    try{
        if(ev.breaking || Vars.net.client() || ev.tile == null) return;
        var core = ev.tile.block(), ut = core.unitType, nm = (ut == null) ? undefined : ACU_MK[ut.name];
        if(nm === undefined || !(core instanceof CoreBlock)) return;
        Groups.player.each(function(p){
            var old = p.unit();
            if(old == null || old.team != ev.team || !old.spawnedByCore) return;
            var om = ACU_MK[old.type.name];
            if(om === undefined || om.mk >= nm.mk) return;
            var nu = ut.create(ev.team);
            nu.set(old.x, old.y);
            nu.rotation = old.rotation;
            nu.spawnedByCore = true;
            nu.health = nu.maxHealth * Math.max(0.1, old.healthf());
            [tpCool, assembly].concat(MOD_DEFS.map(function(d){ return d.st; })).forEach(function(st){
                var d = (st == null) ? 0 : old.getDuration(st);
                if(d > 0) nu.apply(st, d);
            });
            var kn = banKnown[ev.team.id];
            if(kn !== undefined) kn[nu.id] = true;
            nu.add();
            p.unit(nu);
            old.remove();
            Fx.spawn.at(nu.x, nu.y);
        });
    }catch(e){ Log.err("[vg] ACU upgrade: " + e); }
});

// ---------------- ACU modules, teleport and respawn assembly (2.5.0-beta2)
//  * gameplay (install, shield regen, repair, missiles, teleport, assembly) runs on the server/host; clients send
//    requests as "vg-acu" packets ("add <id>", "del <id>", "tp") and draw from the synced statuses
//  * one ACU list for every ACU handler, refreshed every 30 ticks
var banKnown = {}, acuList = [], acuTick = 0, modT = {}, modFail = false, missileT = null, HEAL_COL = Color.valueOf("98ffa9");
Events.on(WorldLoadEvent, function(){ banKnown = {}; acuList = []; acuTick = 0; modT = {}; });
function hasSt(u, st){ return st != null && u.getDuration(st) > 0; }
function modsOf(u){ var o = []; for(var i = 0; i < MOD_DEFS.length; i++) if(hasSt(u, MOD_DEFS[i].st)) o.push(MOD_DEFS[i]); return o; }
function isAcu(u){ return u != null && u.isValid() && ACU_MK[u.type.name] !== undefined; }
function freeFor(team){ return Vars.state.rules.infiniteResources || team.rules().infiniteResources || team.rules().cheat; }
function nearCore(u){ var c = u.closestCore(); return (c != null && u.within(c, MOD_CORE_RANGE + c.block.size * 4)) ? c : null; }
function costOf(d){
    if(d.items == null){
        d.items = [];
        d.cost.forEach(function(c){ var it = Vars.content.item(c[0]); if(it != null) d.items.push({ item: it, n: c[1] }); });
    }
    return d.items;
}
function canPay(core, d){ var it = costOf(d); for(var i = 0; i < it.length; i++) if(!core.items.has(it[i].item, it[i].n)) return false; return true; }
function setShield(u, v){ if(typeof u.shield === "function") u.shield(v); else u.shield = v; }
function fxAt(fx, x, y, rot, col){ if(!Vars.headless) fx.at(x, y, rot, col); }

// returns null on success, otherwise the bundle key of the reason (shown to the local player)
function modAction(p, msg){
    var u = (p == null) ? null : p.unit();
    if(!isAcu(u)) return "vg.mod.noacu";
    var a = String(msg).split(" "), op = a[0];
    if(op == "tp") return teleport(u, p);
    var d = MOD[a[1]];
    if(d === undefined) return "vg.mod.noacu";
    if(op == "del"){ u.unapply(d.st); return null; }
    if(op != "add" || hasSt(u, d.st)) return null;
    if(modsOf(u).length >= MOD_SLOTS) return "vg.mod.full";
    var core = nearCore(u);
    if(core == null) return "vg.mod.nocore";
    if(!freeFor(u.team)){
        if(!canPay(core, d)) return "vg.mod.noitems";
        costOf(d).forEach(function(c){ core.items.remove(c.item, c.n); });
    }
    u.apply(d.st, MOD_FOREVER);
    fxAt(Fx.upgradeCoreBloom, u.x, u.y, u.hitSize / 8, u.team.color);
    var ms = S("acu-module"); if(ms != null && !Vars.headless) ms.at(u.x, u.y, 1);
    return null;
}
function teleport(u, p){
    if(!hasSt(u, MOD.teleport.st)) return "vg.mod.noacu";
    if(hasSt(u, tpCool) || hasSt(u, assembly)) return "vg.tp.cooldown";
    var c = u.closestCore();
    if(c == null) return "vg.mod.nocore";
    fxAt(Fx.teleportOut, u.x, u.y, 0, u.team.color);
    u.set(c.x, c.y);
    u.vel.setZero();
    try{ u.snapInterpolation(); }catch(e){}
    if(p != null){
        p.set(c.x, c.y);
        // remote players own their unit's position, so the server moves it on their side too
        if(Vars.net.server() && p.con != null) Call.setPosition(p.con, c.x, c.y);
    }
    u.apply(tpCool, TP_COOLDOWN);
    fxAt(Fx.teleportActivate, c.x, c.y, 0, u.team.color);
    var s = S("acu-teleport"); if(s != null && !Vars.headless) s.at(c.x, c.y, 1);
    return null;
}

var pktReg = false;
function regPackets(){
    if(pktReg || Vars.netServer == null) return;
    pktReg = true;
    Vars.netServer.addPacketHandler("vg-acu", function(p, msg){
        try{ modAction(p, msg); }catch(e){ Log.err("[vg] ACU module request: " + e); }
    });
}
Events.on(WorldLoadEvent, regPackets);
function request(msg){
    if(Vars.net.client()){ Call.serverPacketReliable("vg-acu", msg); return; }
    var err = modAction(Vars.player, msg);
    if(err != null && !Vars.headless) Vars.ui.showInfoToast(Core.bundle.get(err), 3);
}

// assembly: an ACU spawned by a core of a team whose ACU fell less than 30 s ago waits in the core for the rest
function assembleCheck(u){
    if(assembly == null || !SET.supcom || Vars.net.client() || !isAcu(u) || !u.spawnedByCore) return;
    var ban = banUntil[u.team.id], kn = banKnown[u.team.id];
    if(ban === undefined || ban <= Time.time || (kn !== undefined && kn[u.id])) return;
    if(kn !== undefined) kn[u.id] = true;
    u.apply(assembly, ban - Time.time);
}
Events.on(UnitChangeEvent, function(ev){ try{ var uu = ev.unit; if(uu != null && ACU[uu.type.name]) Log.info("[vg] DIAG change " + uu.type.name + " id=" + uu.id + " valid=" + uu.isValid() + " added=" + uu.isAdded() + " sbc=" + uu.spawnedByCore + " ban=" + banUntil[uu.team.id] + " now=" + Time.time + " known=" + JSON.stringify(banKnown[uu.team.id])); assembleCheck(ev.unit); }catch(e){ Log.err("[vg] ACU assembly: " + e); } });

function missileType(){
    if(missileT == null){
        var src = Vars.content.unit("vg-acu-uef");
        src.weapons.each(function(w){ if(w.name == "vg-acu-uef-launcher") missileT = w.bullet; });
        if(missileT == null) missileT = src.weapons.get(src.weapons.size - 1).bullet;
    }
    return missileT;
}
function repairPulse(u, mk, server){
    var r = (6 + 2 * mk) * 8, f = 0.02 + 0.01 * mk;
    if(!Vars.headless && inView(u.x, u.y, r)) Fx.healWaveDynamic.at(u.x, u.y, r);
    if(!server) return;
    Units.nearby(u.team, u.x, u.y, r, function(o){ if(o.damaged()) o.heal(o.maxHealth * f + 10); });
    Vars.indexer.eachBlock(u.team, u.x, u.y, r, function(b){ return b.damaged(); }, function(b){
        b.heal(b.maxHealth * f);
        if(!Vars.headless) Fx.healBlockFull.at(b.x, b.y, b.block.size, HEAL_COL, b.block);
    });
}
function missileSalvo(u, mk){
    var bt = missileType(), range = bt.speed * bt.lifetime;
    var tg = Units.closestTarget(u.team, u.x, u.y, range);
    if(tg == null) return false;
    var n = mk + 1, base = u.angleTo(tg);
    for(var k = 0; k < n; k++){
        var ang = base + (k - (n - 1) / 2) * 8;
        if(Vars.net.server()) Call.createBullet(bt, u.team, u.x, u.y, ang, bt.damage * u.damageMultiplier, 1, 1);
        else bt.create(u, u.team, u.x, u.y, ang);
    }
    var s = S("acu-missile"); if(s != null && !Vars.headless) s.at(u.x, u.y, Mathf.random(1.05, 1.15), 0.8);
    return true;
}
R(Trigger.update, "acuMods", function(){
    if(modFail || MOD_DEFS.length == 0 || !Vars.state.isGame()) return;
    try{
        var server = !Vars.net.client();
        if((acuTick -= Time.delta) <= 0){
            acuTick = 30;
            var l = [], keep = {};
            Groups.unit.each(function(u){ if(ACU[u.type.name]){ l.push(u); keep[u.id] = true; } });
            acuList = l;
            for(var k in modT) if(!keep[k]) delete modT[k];
            if(server) for(var a = 0; a < l.length; a++) assembleCheck(l[a]);
        }
        if(Vars.state.isPaused()) return;
        for(var i = 0; i < acuList.length; i++){
            var u = acuList[i];
            if(!u.isValid()) continue;
            var t = modT[u.id];
            if(t === undefined) t = modT[u.id] = { rp: 0, ms: 0 };
            var mk = ACU_MK[u.type.name].mk;
            // personal shield: 25% of max health, refills in 10 s
            if(server && hasSt(u, MOD.shield.st)){
                var cap = u.maxHealth * 0.25, sh = F(u, "shield");
                if(sh < cap) setShield(u, Math.min(cap, sh + cap / 600 * Time.delta));
            }
            if(hasSt(u, MOD.repair.st) && (t.rp += Time.delta) >= 90){ t.rp = 0; repairPulse(u, mk, server); }
            // missiles: Mk+1 homing missiles every 2.5 s at the closest enemy in range (ready as soon as one appears)
            if(server && hasSt(u, MOD.missiles.st) && (t.ms += Time.delta) >= 150 && !hasSt(u, assembly)){
                if(missileSalvo(u, mk)) t.ms = 0; else t.ms = 150;
            }
        }
    }catch(e){ modFail = true; Log.err("[vg] ACU modules disabled: " + e); }
});

// assembling ACUs: progress ring in the team colour around the unit (only a handful of ACUs, only while assembling)
var asmFail = false;
R(Trigger.draw, "acuFx", function(){
    if(asmFail || assembly == null || Vars.headless) return;
    try{
        var any = false;
        for(var i = 0; i < acuList.length; i++){
            var u = acuList[i];
            if(!u.isValid() || !inView(u.x, u.y, 48)) continue;
            var rem = u.getDuration(assembly);
            if(!(rem > 0)) continue;
            any = true;
            var r = u.hitSize * 0.9 + 6, p = Mathf.clamp(1 - rem / BAN_TICKS);
            Draw.z(Layer.effect);
            Lines.stroke(2);
            Draw.color(u.team.color, 0.3);
            Lines.circle(u.x, u.y, r);
            Draw.color(assembly.color, 0.6 + 0.3 * Mathf.absin(Time.time, 5, 1));
            Lines.arc(u.x, u.y, r, p, 90);
            for(var j = 0; j < 3; j++){
                var ang = Time.time * 2 + j * 120;
                Lines.lineAngle(u.x + Angles.trnsx(ang, r + 3), u.y + Angles.trnsy(ang, r + 3), ang, 4);
            }
        }
        if(any) Draw.reset();
    }catch(e){ asmFail = true; Draw.reset(); Log.err("[vg] ACU assembly visuals disabled: " + e); }
});

// heavy mech footsteps: sound + light shake when a foot lands (uses the shared ACU list)
var failD = false, steps = {}, stepClean = 0;
R(Trigger.update, "steps", function(){
    if(failD || Vars.headless || !Vars.state.isGame()) return;
    try{
        for(var i = 0; i < acuList.length; i++){
            var u = acuList[i];
            if(!u.isValid() || u.isFlying()) continue;
            var q = Math.floor(u.walkExtend(true)), id = u.id, p = steps[id];
            if(p !== undefined && q != p && (q == 1 || q == 3)){
                var sn = S("acu-step");
                if(sn != null) sn.at(u.x, u.y, Mathf.random(0.9, 1.1), 0.7);
                Effect.shake(0.7, 8, u.x, u.y);
            }
            steps[id] = q;
        }
        if(++stepClean > 1800){ stepClean = 0; steps = {}; }
    }catch(e){
        failD = true;
        Log.err("[vg] mech steps disabled: " + e);
    }
});

// spotter beacon: powered beacons mark enemies within 25 tiles (status applied by the server/host)
var failE = false, spotTick = 0, pingAt = {}, spotLast = -9999;
track("vg-spotter-beacon");
Events.on(WorldLoadEvent, function(){ pingAt = {}; steps = {}; acuList = []; spotLast = -9999; });
R(Trigger.update, "spotter", function(){
    if(failE || spotted == null || !Vars.state.isGame()) return;
    if((spotTick += Time.delta) < 30) return;
    spotTick = 0;
    try{
        var list = blds("vg-spotter-beacon");
        for(var i = 0; i < list.length; i++){
            var b = list[i];
            if(!b.isValid() || !(F(b, "efficiency") > 0.01)) continue;
            var n = 0, bx = b.x, by = b.y;
            Units.nearbyEnemies(b.team, bx, by, 200, function(u){
                n++;
                if(!Vars.net.client()) u.apply(spotted, 75);
            });
            if(n > 0){
                spotLast = Time.time;
                if(!Vars.headless){
                    var k = b.pos(), last = pingAt[k];
                    if(last === undefined || Time.time - last > 360){
                        pingAt[k] = Time.time;
                        var ps = S("spot-ping");
                        if(ps != null) ps.at(bx, by, 1, 0.5);
                    }
                }
            }
        }
    }catch(e){
        failE = true;
        Log.err("[vg] spotter marking disabled: " + e);
    }
});

// rotating blue target brackets over spotted units (skipped entirely while no beacon has marked anything)
var failF = false;
R(Trigger.draw, "spotMarks", function(){
    if(failF || spotted == null || Time.time - spotLast > 120) return;
    try{
        Draw.z(Layer.effect + 1);
        Groups.unit.each(function(u){
            if(!u.hasEffect(spotted) || !inView(u.x, u.y, 16)) return;
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
// EMP shells are handled by the shared impact pass below (dsInit registers them with empFx), so all impact
// mechanics share one scan of the bullets per frame
var EMP_DEFS = [["vg-mantis", 40], ["vg-hydra", 22]];

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
    // Requiem quantum shell: same freeze, wider
    var req = Vars.content.block("vg-requiem");
    if(req != null && qm != null){
        var rqt = req.ammoTypes.get(qm);
        if(rqt != null) dsT.put(rqt, { r: 112, k: 0.02, d: 180, c: Color.valueOf("c890ff") });
    }
    dsDone = true;
    // EMP shells (Mantis / Hydra on magnets): enemy powered buildings slowed to 35% for 4 s, blue shock ring
    var mag = Vars.content.item("vg-magnet");
    for(var ei = 0; ei < EMP_DEFS.length; ei++){
        var ebl = Vars.content.block(EMP_DEFS[ei][0]);
        if(ebl == null || mag == null) continue;
        var ebt = ebl.ammoTypes.get(mag);
        if(ebt != null) dsT.put(ebt, { r: EMP_DEFS[ei][1], k: 0.35, d: 240, fx: empFx });
    }
}
try{ Events.on(ContentInitEvent, function(){ try{ dsInit(); }catch(e){ Log.err("[vg] T4 init: " + e); } }); }catch(e){}
R(Trigger.update, "impacts", function(){
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
            if(cfg.fx != null) cfg.fx.at(x, y, cfg.r); else dsFx.at(x, y, cfg.r, cfg.c);
            if(Vars.net.client()) return;
            Vars.indexer.eachBlock(null, x, y, cfg.r, function(bd){ return bd.team != tm; }, function(bd){
                try{ bd.applySlowdown(cfg.k, cfg.d); }catch(e2){}
            });
        });
        if(++dsClean > 600){ dsClean = 0; for(var k in dsSeen){ if(Time.time - dsSeen[k] > 300) delete dsSeen[k]; } }
    }catch(e){ dsFail = true; Log.err("[vg] impact script disabled: " + e); }
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
// Interceptor: every `reload` ticks a powered building destroys the nearest enemy shell within range,
// except shells of the `immune` blocks. Used by the Quantum Interceptor (T5) and the Seraphim Net (T6).
function interceptor(blockName, immuneBlocks){
    var st = { block: null, immune: null, fail: false, timers: {} };
    track(blockName);
    function init(){
        st.block = Vars.content.block(blockName);
        st.immune = new ObjectSet();
        immuneBlocks.forEach(function(n){
            var bl = Vars.content.block(n);
            if(bl == null || bl.ammoTypes == null) return;
            bl.ammoTypes.values().toSeq().each(function(bt){
                st.immune.add(bt);
                if(bt.fragBullet != null) st.immune.add(bt.fragBullet);
            });
        });
    }
    Events.on(WorldLoadEvent, function(){ st.timers = {}; });
    R(Trigger.update, blockName.substring(3), function(){
        if(st.fail || !Vars.state.isPlaying() || Vars.net.client()) return;
        try{
            if(st.block == null){ init(); if(st.block == null){ st.fail = true; return; } }
            var blk = st.block, list = blds(blockName);
            for(var i = 0; i < list.length; i++){
                var bd = list[i];
                if(!bd.isValid()) continue;
                // efficiency is 0 while vanilla point defence has no hittable target, so use the powered state instead
                var k = bd.pos(), t = (st.timers[k] || 0) + Time.delta * bd.potentialEfficiency;
                if(t < blk.reload){ st.timers[k] = t; continue; }
                var best = null, bestD = blk.range * blk.range, tm = bd.team, bx = bd.x, by = bd.y;
                Groups.bullet.intersect(bx - blk.range, by - blk.range, blk.range * 2, blk.range * 2, function(b){
                    if(b.team == tm || st.immune.contains(b.type)) return;
                    var d2 = (b.x - bx) * (b.x - bx) + (b.y - by) * (b.y - by);
                    if(d2 < bestD){ bestD = d2; best = b; }
                });
                if(best == null){ st.timers[k] = t; continue; }
                st.timers[k] = 0;
                qiFx.at(bx, by, 0, blk.color, new Vec2(best.x, best.y));
                Fx.absorb.at(best.x, best.y, 0, blk.color);
                blk.shootSound.at(bx, by, Mathf.random(0.95, 1.05));
                best.remove();
            }
        }catch(e){ st.fail = true; Log.err("[vg] " + blockName + " disabled: " + e); }
    });
}
interceptor("vg-quantum-interceptor", ["vg-tempest", "vg-requiem"]);

// ---------------- Vanguard Arsenal 2.5 - T6 scripts (Seraphim)
//  * Requiem shells get the ballistic shadow / impact marker / incoming whistle; quantum shells freeze (see dsInit)
//  * Seraphim Net: the interceptor above with nothing immune (T5-T6 and singular shells included)
//  * Chronofield: powered fields put 'chrono-slow' (speed and fire rate x0.3) on enemy units in range (server/host)
//  * Seraphim Dome: singular shells are not absorbable, so every vanilla shield ignores them; the Dome alone
//    catches them here and takes x4 their damage
ARTY["vg-requiem"] = { col: Color.valueOf("c890ff"), whistle: "scorpion-whistle", h: 40 };
interceptor("vg-seraphim-net", []);

var chronoBlock = null, chronoSt = null, chronoFail = false, chronoTick = 0;
track("vg-chronofield");
R(Trigger.update, "chronofield", function(){
    if(chronoFail || !Vars.state.isPlaying() || Vars.net.client()) return;
    if((chronoTick += Time.delta) < 20) return;
    chronoTick = 0;
    try{
        if(chronoBlock == null){
            chronoBlock = Vars.content.block("vg-chronofield");
            chronoSt = Vars.content.getByName(ContentType.status, "vg-chrono-slow");
            if(chronoBlock == null || chronoSt == null){ chronoFail = true; return; }
        }
        var list = blds("vg-chronofield");
        for(var i = 0; i < list.length; i++){
            var bd = list[i];
            if(!bd.isValid() || !(F(bd, "efficiency") > 0.01)) continue;
            Units.nearbyEnemies(bd.team, bd.x, bd.y, chronoBlock.range, function(u){ u.apply(chronoSt, 40); });
        }
    }catch(e){ chronoFail = true; Log.err("[vg] chronofield disabled: " + e); }
});

var domeBlock = null, singularT = null, domeFail = false, DOME_COL = Color.valueOf("c890ff");
track("vg-seraphim-dome");
function domeInit(){
    domeBlock = Vars.content.block("vg-seraphim-dome");
    singularT = new ObjectSet();
    var rq = Vars.content.block("vg-requiem"), sc = Vars.content.item("vg-singular-core");
    if(rq != null && sc != null){
        var bt = rq.ammoTypes.get(sc);
        if(bt != null) singularT.add(bt);
    }
}
R(Trigger.update, "dome", function(){
    if(domeFail || !Vars.state.isPlaying() || Vars.net.client()) return;
    try{
        if(domeBlock == null){ domeInit(); if(domeBlock == null || singularT.size == 0){ domeFail = true; return; } }
        var list = blds("vg-seraphim-dome");
        for(var i = 0; i < list.length; i++){
            var bd = list[i];
            if(!bd.isValid() || bd.broken) continue;
            var r = bd.realRadius();
            if(!(r > 0.001)) continue;
            var tm = bd.team, x = bd.x, y = bd.y;
            Groups.bullet.intersect(x - r, y - r, r * 2, r * 2, function(b){
                if(b.team == tm || !singularT.contains(b.type)) return;
                if(!Intersector.isInRegularPolygon(domeBlock.sides, x, y, r, domeBlock.shieldRotation, b.x, b.y)) return;
                Fx.absorb.at(b.x, b.y, 0, DOME_COL);
                bd.hit = 1;
                bd.buildup += b.damage * 4;
                b.absorb();
            });
        }
    }catch(e){ domeFail = true; Log.err("[vg] seraphim dome disabled: " + e); }
});

// ---------------- settings page (client only): Settings -> Vanguard Arsenal
Events.on(ClientLoadEvent, function(){
    try{
        Vars.ui.settings.addCategory(Core.bundle.get("vg.settings"), Icon.settings, function(t){
            t.checkPref("vg-supcom", true);
            t.checkPref("vg-shellfx", true);
            t.checkPref("vg-acu-defeat", false);
        });
    }catch(e){ Log.err("[vg] settings page: " + e); }
});

// ---------------- ACU panel (client only): module slots, modules dialog, teleport, assembly timer.
// Left edge, vertically centred (free on desktop and mobile); rebuilt only when what it shows changes.
function myAcu(){ var u = Vars.player.unit(); return isAcu(u) ? u : null; }
function secs(ticks){ return Math.ceil(ticks / 60); }
function showModules(){
    var dlg = new BaseDialog(Core.bundle.get("vg.mod.title"));
    var rebuild = function(){
        dlg.cont.clear();
        var u = myAcu();
        if(u == null){ dlg.hide(); return; }
        var mods = modsOf(u), core = nearCore(u), free = freeFor(u.team);
        dlg.cont.add(Core.bundle.format("vg.mod.slots", mods.length, MOD_SLOTS)).left().row();
        dlg.cont.add(core == null ? "[scarlet]" + Core.bundle.get("vg.mod.nocore") : "[lightgray]" + Core.bundle.get("vg.mod.atcore")).left().padBottom(6).row();
        dlg.cont.pane(function(list){
            MOD_DEFS.forEach(function(d){
                var on = hasSt(u, d.st);
                list.table(Styles.black6, function(r){
                    r.margin(8).left();
                    r.image(d.st.uiIcon).size(48).padRight(10);
                    r.table(function(info){
                        info.left();
                        info.add((on ? "[accent]" : "") + d.st.localizedName).left().row();
                        info.add("[lightgray]" + d.st.description).wrap().width(Math.min(420, Core.graphics.getWidth() * 0.45)).left().row();
                        info.table(function(c){
                            c.left();
                            costOf(d).forEach(function(it){
                                var ok = free || (core != null && core.items.has(it.item, it.n));
                                c.image(it.item.uiIcon).size(20).padRight(2);
                                c.add((ok ? "" : "[scarlet]") + it.n).padRight(10);
                            });
                        }).left().padTop(4);
                    }).growX().left();
                    var btn = r.button(Core.bundle.get(on ? "vg.mod.remove" : "vg.mod.install"), function(){
                        request((on ? "del " : "add ") + d.id);
                        Time.run(10, rebuild);
                    }).width(140).height(48);
                    btn.disabled(!on && (mods.length >= MOD_SLOTS || core == null || (!free && !canPay(core, d))));
                }).growX().pad(3).row();
            });
        }).growX().maxHeight(Core.graphics.getHeight() * 0.7);
    };
    rebuild();
    dlg.addCloseButton();
    dlg.show();
}
var hudFail = false, hudKey = "";
function hudBuild(p){
    var u = myAcu();
    var key = "";
    if(u != null){
        key = u.id + "|" + modsOf(u).map(function(d){ return d.id; }).join(",") + "|" + secs(u.getDuration(tpCool)) + "|" + secs(u.getDuration(assembly));
    }
    if(key == hudKey) return;
    hudKey = key;
    p.clear();
    if(u == null) return;
    var mods = modsOf(u);
    p.table(function(slots){
        for(var i = 0; i < MOD_SLOTS; i++){
            var d = mods[i];
            if(d != null) slots.image(d.st.uiIcon).size(32).pad(2);
            else slots.image(Tex.whiteui).color(Color.valueOf("3a3a44")).size(32).pad(2);
            slots.row();
        }
    });
    p.row();
    p.button(Icon.upgrade, Styles.cleari, function(){ showModules(); }).size(44).padTop(2).name("vg-acu-modules");
    if(hasSt(u, MOD.teleport.st)){
        p.row();
        var cd = u.getDuration(tpCool);
        var tb = p.button(Icon.home, Styles.cleari, function(){
            fxAt(Fx.teleportOut, u.x, u.y, 0, u.team.color);
            request("tp");
        }).size(44);
        tb.disabled(cd > 0 || hasSt(u, assembly));
        if(cd > 0){ p.row(); p.add("[lightgray]" + secs(cd) + Core.bundle.get("vg.sec")); }
    }
    var asm = u.getDuration(assembly);
    if(asm > 0){ p.row(); p.add("[accent]" + Core.bundle.format("vg.mod.assembly", secs(asm))).padTop(4); }
}
Events.on(ClientLoadEvent, function(){
    try{
        // built by hand: Group.fill(function) is ambiguous for Rhino (fill(DrawRect) / fill(Cons<Table>))
        var t = new Table();
        t.setFillParent(true);
        t.name = "vg-acu-panel";
        t.left();
        t.visible(function(){ return !hudFail && Vars.ui.hudfrag.shown && Vars.state.isGame() && myAcu() != null; });
        t.table(Styles.black6, function(p){
            p.margin(4);
            p.update(function(){
                if(hudFail) return;
                try{ hudBuild(p); }catch(e){ hudFail = true; Log.err("[vg] ACU panel disabled: " + e); }
            });
        });
        Vars.ui.hudGroup.addChild(t);
    }catch(e){ Log.err("[vg] ACU panel: " + e); }
});
