// Vanguard Arsenal in-game test stand (NOT shipped with the mod).
// Builds a test world with every vg block, a firing range and mechanic labs, takes screenshots from the
// real renderer, measures the JS/engine mechanics and exits. Output: <data>/vgtest/*.png + manifest.json
var OUT = Core.settings.getDataDirectory().child("vgtest");
var W = 330, H = 340, SHOW_W = 232;
var CAT_ORDER = ["turret", "defense", "effect", "crafting", "production", "power", "units", "distribution", "liquid", "logic"];
var manifest = { blocks: [], shots: [], errors: [] };
var shots = [], shotIdx = 0, armedFrame = -1, t0 = -1, done = false, feedTick = 0, waveTick = 0;
var turrets = [];

function L(m){ Log.info("[vgtest] " + m); }
function E(m){ Log.err("[vgtest] " + m); manifest.errors.push(String(m)); }
function blk(n){ return Vars.content.block(n); }
function statusByName(n){ return Vars.content.getByName(ContentType.status, n); }

function vgBlocks(){
    var out = [];
    Vars.content.blocks().each(function(b){
        if(b.minfo != null && b.minfo.mod != null && b.minfo.mod.name == "vg") out.push(b);
    });
    return out;
}

function off(size){ return Math.floor((size - 1) / 2); }

function place(block, bx, by, team, rot){
    if(block == null){ E("place: null block at " + bx + "," + by); return null; }
    var t = Vars.world.tile(bx + off(block.size), by + off(block.size));
    if(t == null) return null;
    t.setBlock(block, team, rot || 0);
    return t.build;
}

function addShot(name, at, cx, cy, scale, gif){
    shots.push({ name: name, at: at, cx: cx, cy: cy, scale: scale, gif: !!gif });
}

function setup(){
    try{
        Vars.world.loadGenerator(W, H, function(tiles){
            tiles.each(function(x, y){
                var floor = (y >= 88 && x < SHOW_W) ? Blocks.darksand : Blocks.stone;
                tiles.set(x, y, new Tile(x, y, floor, Blocks.air, Blocks.air));
            });
        });
        var r = new Rules();
        r.infiniteResources = true;
        r.waves = false;
        r.fog = false;
        r.lighting = false;
        r.teams.get(Team.sharded).cheat = true;
        r.teams.get(Team.crux).cheat = true;
        Vars.state.rules = r;
        Vars.logic.play();
        Vars.renderer.minZoom = 0.5;
        Vars.ui.hudfrag.shown = false;
        place(Blocks.coreShard, 2, H - 6, Team.sharded, 0);

        layoutShowcase();
        layoutRange();
        layoutMech();
        layoutShieldLab();
        layoutInterceptLab();
        layoutTempestLab();
        layoutT6Labs();
        layoutBetaLabs();
        planShots();
        t0 = Time.time;
        L("setup done: " + manifest.blocks.length + " blocks, " + shots.length + " shots");
    }catch(e){
        E("setup failed: " + e);
        finish();
    }
}

// ------------------------------------------------------------------ showcase: every vg block on a grid
function layoutShowcase(){
    var list = vgBlocks();
    list.sort(function(a, b){
        var ca = CAT_ORDER.indexOf(String(a.category)), cb = CAT_ORDER.indexOf(String(b.category));
        if(a instanceof OreBlock) ca = 99;
        if(b instanceof OreBlock) cb = 99;
        if(ca != cb) return ca - cb;
        return a.size - b.size;
    });
    var x = 6, y = 6, rowH = 0, gap = 2, maxX = SHOW_W - 6, prevCat = null;
    for(var i = 0; i < list.length; i++){
        var b = list[i];
        var cat = (b instanceof OreBlock) ? "ore" : String(b.category);
        var s = (b instanceof OreBlock) ? 3 : b.size;
        if(prevCat != null && cat != prevCat){ x += 3; }
        if(x + s > maxX){ x = 6; y += rowH + gap; rowH = 0; }
        try{
            if(b instanceof OreBlock){
                for(var dx = 0; dx < 3; dx++) for(var dy = 0; dy < 3; dy++){
                    var ot = Vars.world.tile(x + dx, y + dy);
                    if(b.wallOre) ot.setBlock(Blocks.stoneWall);
                    ot.setOverlay(b);
                }
            }else{
                var bd = place(b, x, y, Team.sharded, 0);
                if(bd == null) E("place returned null: " + b.name);
            }
            manifest.blocks.push({ name: String(b.name), x: x, y: y, size: s, cat: cat });
        }catch(e){ E("place " + b.name + ": " + e); }
        x += s + gap;
        rowH = Math.max(rowH, s);
        prevCat = cat;
    }
    var ux = 8, uy = y + rowH + 4;
    ["vg-acu-uef", "vg-acu-cybran", "vg-engineer"].forEach(function(n){
        var u = Vars.content.unit(n);
        if(u == null){ E("missing unit " + n); return; }
        try{ u.spawn(Team.sharded, ux * 8, uy * 8); manifest.blocks.push({ name: n, x: ux, y: uy, size: 2, cat: "unit" }); }catch(e){ E("spawn " + n + ": " + e); }
        ux += 6;
    });
    manifest.showcaseTop = uy + 4;
}

// ------------------------------------------------------------------ firing range: all turrets vs enemy walls and waves
function heaters(b, x, row){
    if(!(b.heatRequirement > 0)) return;
    var hb = blk("vg-plasma-heater");
    var n = Math.ceil(b.heatRequirement / 20), x0 = x + Math.floor((b.size - 3 * n) / 2);
    for(var i = 0; i < n; i++) place(hb, x0 + i * 3, row - 3, Team.sharded, 1);
}

function layoutRange(){
    var row = 96, x = 8;
    vgBlocks().forEach(function(b){
        if(String(b.category) != "turret") return;
        var bd = place(b, x, row, Team.sharded, 1);
        if(bd != null) turrets.push(bd);
        heaters(b, x, row);
        manifest.blocks.push({ name: String(b.name), x: x, y: row, size: b.size, cat: "range" });
        x += b.size + 4;
    });
    ["vg-spotter-beacon", "vg-recon-radar"].forEach(function(n){
        var b = blk(n);
        if(b == null){ E("missing " + n); return; }
        place(b, x, row, Team.sharded, 0);
        manifest.blocks.push({ name: n, x: x, y: row, size: b.size, cat: "range" });
        x += b.size + 4;
    });
    manifest.rangeEnd = x;
    buildTargets();
}

function buildTargets(){
    var walls = [[106, 110], [134, 142]];
    for(var w = 0; w < walls.length; w++){
        for(var y = walls[w][0]; y < walls[w][1]; y += 3){
            for(var x = 6; x < manifest.rangeEnd + 4; x += 3){
                var t = Vars.world.tile(x, y);
                if(t != null && t.build == null) t.setBlock(Blocks.thoriumWallLarge, Team.crux, 0);
            }
        }
    }
}

function spawnEnemies(){
    var types = [UnitTypes.dagger, UnitTypes.mace, UnitTypes.flare, UnitTypes.horizon];
    for(var i = 0; i < 8; i++){
        var t = types[i % types.length];
        t.spawn(Team.crux, (10 + Math.random() * (manifest.rangeEnd - 10)) * 8, (112 + Math.random() * 18) * 8);
    }
}

function feed(){
    for(var i = 0; i < turrets.length; i++){
        var b = turrets[i];
        if(b == null || !b.isValid()) continue;
        var am = b.block.ammoTypes;
        if(am == null || am.keys == undefined) continue;
        var keys = am.keys().toSeq();
        if(keys.size == 0) continue;
        var phase = Math.floor((Time.time - t0) / 400);
        var it = keys.get((i + phase) % keys.size);
        for(var n = 0; n < 12 && b.acceptItem(b, it); n++) b.handleItem(b, it);
    }
}

function feedOnly(b, name){
    var it = Vars.content.item(name);
    if(b == null || !b.isValid() || it == null) return;
    for(var n = 0; n < 12 && b.acceptItem(b, it); n++) b.handleItem(b, it);
}

// ------------------------------------------------------------------ mechanics lab (pinned, unkillable enemy dummies)
var MX = 100;
var dummies = [], mech = { spottedMax: 0, disarmedMax: 0, empSlowMax: 0, monolithSlowMax: 0, acuWallsBefore: -1, acuWallsAfter: -1, acuKilled: false,
    haloFired: false, tempestFrozenMax: 0, stasisMax: 0, tempestHeat: -1 };
var acuWalls = [], acuUnit = null, poly = null, eng = null;
function wallRing(cx, cy, rad){
    for(var dx = -rad; dx <= rad; dx += 2) for(var dy = -rad; dy <= rad; dy += 2){
        if(Math.abs(dx) < rad && Math.abs(dy) < rad) continue;
        var t = Vars.world.tile(cx + dx, cy + dy);
        var corner = Math.abs(dx) == rad && Math.abs(dy) == rad;
        if(t != null && t.build == null) t.setBlock(corner ? Blocks.duo : Blocks.thoriumWall, Team.crux, 0);
    }
}
function dummy(x, y, list, type){
    type = type || UnitTypes.dagger;
    var u = type.spawn(Team.crux, x * 8, y * 8);
    var d = { u: u, x: x * 8, y: y * 8, type: type };
    dummies.push(d);
    if(list) list.push(d);
    wallRing(x, y, 3);
}
function layoutMech(){
    place(blk("vg-spotter-beacon"), MX + 150, 140, Team.sharded, 0);
    dummy(MX + 153, 140); dummy(MX + 150, 145);
    place(blk("vg-suppressor"), MX + 162, 130, Team.sharded, 0);
    dummy(MX + 168, 131); dummy(MX + 163, 137);
    mech.mantis = place(blk("vg-mantis"), MX + 176, 102, Team.sharded, 1);
    mech.monolith = place(blk("vg-monolith"), MX + 196, 102, Team.sharded, 1);
    place(blk("vg-plasma-heater"), MX + 197, 99, Team.sharded, 1);
    dummy(MX + 180, 128); dummy(MX + 200, 142);
    for(var dx = -4; dx <= 4; dx += 2) for(var dy = -4; dy <= 4; dy += 2){
        if(dx == 0 && dy == 0) continue;
        var t = Vars.world.tile(MX + 116 + dx, 150 + dy);
        if(t != null){ t.setBlock(Blocks.thoriumWall, Team.crux, 0); acuWalls.push(t.build); }
    }
    acuUnit = Vars.content.unit("vg-acu-uef").spawn(Team.sharded, (MX + 116) * 8, 150 * 8);
    // SupCom build rule: a non-cheat team owning a BKM core; plans are added in the draw phase (see postDraw)
    place(blk("vg-core-uef"), 112, 146, Team.green, 0);
    poly = UnitTypes.poly.spawn(Team.green, 130 * 8, 152 * 8);
    eng = Vars.content.unit("vg-engineer").spawn(Team.green, 134 * 8, 152 * 8);
    eng.addBuild(new BuildPlan(134, 155, 0, Blocks.copperWall));
}
function wallHp(){ var s = 0; for(var i = 0; i < acuWalls.length; i++){ var w = acuWalls[i]; s += (w != null && w.isValid()) ? w.health : 0; } return s; }

// ------------------------------------------------------------------ shield lab: how much a Monolith shell drains a Citadel
var shield = { b: null, jumps: [], last: 0, fired: 0 };
var shooter = null; // crux owner entity for bullets spawned by the labs (a null owner makes create() ambiguous in Rhino)
function owner(){
    if(shooter == null || !shooter.isValid()){ var t = Vars.world.tile(W - 3, H - 3); t.setBlock(Blocks.thoriumWall, Team.crux, 0); shooter = t.build; }
    return shooter;
}
function layoutShieldLab(){
    shield.b = place(blk("vg-citadel"), 250, 150, Team.sharded, 0);
}
function shieldUpdate(t){
    var b = shield.b;
    if(b == null || !b.isValid()) return;
    var bu = b.buildup;
    if(bu - shield.last > 300) shield.jumps.push(Math.round(bu - shield.last));
    shield.last = bu;
    if(t > 240 && shield.fired < 3 && (t - 240) > shield.fired * 90){
        var mon = blk("vg-monolith"), bt = mon.ammoTypes.get(Vars.content.item("vg-iridium"));
        bt.create(owner(), Team.crux, (251.5 + 26) * 8, 151.5 * 8, 180);
        shield.fired++;
    }
}

// ------------------------------------------------------------------ intercept lab: Quantum Interceptor vs T2-T4 shells, T5 immune
var qi = { b: null, tracked: [], stats: {} };
function layoutInterceptLab(){
    qi.b = place(blk("vg-quantum-interceptor"), 300, 200, Team.sharded, 0);
}
function qiSpawn(kind, block, item, y){
    var bt = blk(block).ammoTypes.get(Vars.content.item(item));
    var b = bt.create(owner(), Team.crux, 262 * 8, y * 8, 0);
    qi.tracked.push({ b: b, kind: kind, life: b.lifetime });
    if(qi.stats[kind] == null) qi.stats[kind] = { spawned: 0, intercepted: 0 };
    qi.stats[kind].spawned++;
}
function qiUpdate(t){
    if(t > 200 && t < 1000 && Math.floor(t) % 45 == 0 && qi.lastSpawn != Math.floor(t)){
        qi.lastSpawn = Math.floor(t);
        var k = Math.floor(t / 45) % 3;
        if(k == 0) qiSpawn("redoubt-T2", "vg-redoubt", "vg-charge", 201);
        else if(k == 1) qiSpawn("tempest-T5", "vg-tempest", "vg-iridium", 203);
        else qiSpawn("requiem-T6", "vg-requiem", "vg-singular-core", 205);
    }
    for(var i = qi.tracked.length - 1; i >= 0; i--){
        var e = qi.tracked[i];
        if(e.b.isAdded()) continue;
        if(e.b.time < e.life - 3) qi.stats[e.kind].intercepted++;
        qi.tracked.splice(i, 1);
    }
}

// ------------------------------------------------------------------ tempest lab: quantum shells freeze buildings + stasis on units
var tl = { b: null, dummies: [] };
function layoutTempestLab(){
    var qt = blk("vg-tempest").ammoTypes.get(Vars.content.item("vg-quantum-matrix")), rd = blk("vg-redoubt").ammoTypes.get(Vars.content.item("vg-charge"));
    L("tempest quantum status=" + (qt.status == null ? "null" : qt.status.name) + " dur=" + qt.statusDuration + " radius=" + qt.splashDamageRadius + "; redoubt charge damage=" + rd.damage + " splash=" + rd.splashDamage);
    tl.b = place(blk("vg-tempest"), 282, 10, Team.sharded, 1);
    heaters(blk("vg-tempest"), 282, 10);
    // reigns (24k HP) survive a full salvo, so the stasis status can be observed on the same unit
    dummy(286, 70, tl.dummies, UnitTypes.reign); dummy(279, 74, tl.dummies, UnitTypes.reign);
}
function tempestUpdate(){
    feedOnly(tl.b, "vg-quantum-matrix");
    var st = statusByName("vg-quantum-stasis"), ns = 0;
    for(var i = 0; i < tl.dummies.length; i++) if(st != null && tl.dummies[i].u.hasEffect(st)) ns++;
    mech.stasisMax = Math.max(mech.stasisMax, ns);
    var fr = 0;
    Vars.indexer.eachBlock(Team.crux, 283 * 8, 72 * 8, 12 * 8, function(b){ return true; }, function(b){ if(b.timeScale() < 0.05) fr++; });
    mech.tempestFrozenMax = Math.max(mech.tempestFrozenMax, fr);
    if(tl.b != null && tl.b.isValid()) mech.tempestHeat = Math.max(mech.tempestHeat, tl.b.heatReq);
}

function mechUpdate(){
    for(var i = 0; i < dummies.length; i++){
        var d = dummies[i];
        if(d.u == null || !d.u.isValid()){ d.u = d.type.spawn(Team.crux, d.x, d.y); }
        d.u.set(d.x, d.y); d.u.vel.setZero(); d.u.health = d.u.maxHealth;
    }
    feedOnly(mech.mantis, "vg-magnet");
    feedOnly(mech.monolith, "vg-magnet");
    var sp = statusByName("vg-spotted"), ds = statusByName("vg-disarmed"), ns = 0, nd = 0;
    for(var j = 0; j < dummies.length; j++){
        var du = dummies[j].u;
        if(sp != null && du.hasEffect(sp)) ns++;
        if(ds != null && du.hasEffect(ds)) nd++;
    }
    mech.spottedMax = Math.max(mech.spottedMax, ns);
    mech.disarmedMax = Math.max(mech.disarmedMax, nd);
    var s35 = 0, s30 = 0;
    Groups.build.each(function(b){
        if(b.team != Team.crux) return;
        var ts = b.timeScale();
        if(Math.abs(ts - 0.35) < 0.01) s35++;
        if(Math.abs(ts - 0.3) < 0.01) s30++;
        if(!mech.haloFired && b.block != null && b.block.name == "vg-halo" && b.bullets != null && b.bullets.size > 0) mech.haloFired = true;
    });
    Groups.build.each(function(b){
        if(!mech.haloFired && b.team == Team.sharded && b.block.name == "vg-halo" && b.bullets.size > 0) mech.haloFired = true;
    });
    mech.empSlowMax = Math.max(mech.empSlowMax, s35); mech.monolithSlowMax = Math.max(mech.monolithSlowMax, s30);
    var t = Time.time - t0;
    if(!mech.acuKilled && t > 400){ mech.acuWallsBefore = wallHp(); acuUnit.kill(); mech.acuKilled = true; }
    if(mech.acuKilled && t > 460 && mech.acuWallsAfter < 0) mech.acuWallsAfter = wallHp();
    shieldUpdate(t);
    qiUpdate(t);
    tempestUpdate();
    t6Update(t);
    betaUpdate(t);
}

function mechReport(){
    mech.polyPlans = poly.plans.size;
    mech.polyBuilt = String(Vars.world.tile(130, 155).block().name);
    mech.engPlans = eng.plans.size;
    mech.engBuilt = String(Vars.world.tile(134, 155).block().name);
    mech.shieldJumps = shield.jumps;
    mech.intercept = qi.stats;
    t6Report();
    betaReport();
    delete mech.mantis; delete mech.monolith;
    manifest.mech = mech;
    L("mech " + JSON.stringify(mech));
}

// ------------------------------------------------------------------ T6 labs (band y 250-340)
//  chronofield: pinned dummies inside its 60-tile field must get vg-chrono-slow
//  seraphim net: T5 and T6 (singular) shells fired past it must all be destroyed
//  aegis vs dome: singular shells pass through the Aegis untouched; the Dome absorbs them with x4 buildup
//  annihilation reactor: running reactor inside a ring of enemy walls is destroyed on a timer -> blast damage
//  gravity extractor on singularite ore; T6 crafters in the showcase must produce (cheat team, no inputs needed)
var t6 = { chrono: null, chronoDummies: [], net: null, netTracked: [], netStats: {}, aegis: null, aegisMax: 0, aegisShells: [],
    aegisPassed: 0, aegisSpawned: 0, dome: null, domeJumps: [], domeLast: 0, domeShells: [], domeSpawned: 0, domeLeaked: 0,
    reactor: null, reactorWalls: [], reactorHeat: 0, wallsBefore: -1, wallsAfter: -1, reactorKilled: false, grav: null, obeliskFired: false };
function layoutT6Labs(){
    t6.chrono = place(blk("vg-chronofield"), 10, 290, Team.sharded, 0);
    dummy(13, 318, t6.chronoDummies); dummy(36, 300, t6.chronoDummies);
    t6.net = place(blk("vg-seraphim-net"), 80, 300, Team.sharded, 0);
    t6.aegis = place(blk("vg-aegis"), 165, 285, Team.sharded, 0);
    t6.dome = place(blk("vg-seraphim-dome"), 240, 290, Team.sharded, 0);
    t6.reactor = place(blk("vg-annihilation-reactor"), 300, 296, Team.sharded, 0);
    var rc = 303, rr = 9;
    for(var dx = -rr; dx <= rr; dx += 2) for(var dy = -rr; dy <= rr; dy += 2){
        if(Math.abs(dx) < rr && Math.abs(dy) < rr) continue;
        var tw = Vars.world.tile(rc + dx, 299 + dy);
        if(tw != null && tw.build == null){ tw.setBlock(Blocks.thoriumWall, Team.crux, 0); t6.reactorWalls.push(tw.build); }
    }
    var ore = blk("vg-ore-singularite");
    for(var ox = 0; ox < 6; ox++) for(var oy = 0; oy < 6; oy++) Vars.world.tile(288 + ox, 255 + oy).setOverlay(ore);
    t6.grav = place(blk("vg-gravity-extractor"), 288, 255, Team.sharded, 0);
}
function t6Shell(block, item, x, y, angle){
    return blk(block).ammoTypes.get(Vars.content.item(item)).create(owner(), Team.crux, x * 8, y * 8, angle);
}
function reactorWallHp(){ var s = 0; t6.reactorWalls.forEach(function(w){ s += (w != null && w.isValid()) ? w.health : 0; }); return s; }
function t6Update(t){
    var st = statusByName("vg-chrono-slow"), n = 0;
    t6.chronoDummies.forEach(function(d){ if(st != null && d.u.hasEffect(st)) n++; });
    mech.chronoMax = Math.max(mech.chronoMax || 0, n);
    // net: one shell every 300 ticks (net reload is 240), alternating T6 singular and T5 iridium, flying west past it
    var ns = t6.netSpawned || 0;
    if(t > 260 + ns * 300 && ns < 4){
        t6.netSpawned = ns + 1;
        var kind = (ns % 2 == 0) ? "requiem-T6" : "tempest-T5";
        var b = kind == "tempest-T5" ? t6Shell("vg-tempest", "vg-iridium", 100, 312, 180) : t6Shell("vg-requiem", "vg-singular-core", 100, 312, 180);
        t6.netTracked.push({ b: b, kind: kind, life: b.lifetime });
        if(t6.netStats[kind] == null) t6.netStats[kind] = { spawned: 0, intercepted: 0 };
        t6.netStats[kind].spawned++;
    }
    for(var i = t6.netTracked.length - 1; i >= 0; i--){
        var e = t6.netTracked[i];
        if(e.b.isAdded()) continue;
        if(e.b.time < e.life - 3) t6.netStats[e.kind].intercepted++;
        t6.netTracked.splice(i, 1);
    }
    // aegis / dome: three singular shells each
    if(t > 250 && t6.aegisSpawned < 3 && t - 250 > t6.aegisSpawned * 120){
        t6.aegisShells.push(t6Shell("vg-requiem", "vg-singular-core", 168.5 - 34, 288.5, 0)); t6.aegisSpawned++;
        t6.domeShells.push(t6Shell("vg-requiem", "vg-singular-core", 244.5 + 46, 294.5, 180)); t6.domeSpawned++;
    }
    if(t6.aegis != null && t6.aegis.isValid()) t6.aegisMax = Math.max(t6.aegisMax, t6.aegis.buildup);
    for(var a = t6.aegisShells.length - 1; a >= 0; a--){
        var sb = t6.aegisShells[a];
        if(!sb.isAdded()){ t6.aegisShells.splice(a, 1); continue; }
        if(sb.x > (168.5 + 30) * 8){ t6.aegisPassed++; sb.remove(); t6.aegisShells.splice(a, 1); }
    }
    for(var d2 = t6.domeShells.length - 1; d2 >= 0; d2--){
        var db = t6.domeShells[d2];
        if(!db.isAdded()){ t6.domeShells.splice(d2, 1); continue; }
        if(db.x < 244.5 * 8){ t6.domeLeaked++; db.remove(); t6.domeShells.splice(d2, 1); }
    }
    if(t6.dome != null && t6.dome.isValid()){
        var bu = t6.dome.buildup;
        if(bu - t6.domeLast > 1000) t6.domeJumps.push(Math.round(bu - t6.domeLast));
        t6.domeLast = bu;
    }
    // annihilation reactor
    if(t6.reactor != null && t6.reactor.isValid()) t6.reactorHeat = Math.max(t6.reactorHeat, t6.reactor.heat);
    if(!t6.reactorKilled && t > 520){ t6.wallsBefore = reactorWallHp(); t6.reactorWarmup = t6.reactor.warmup; t6.reactor.kill(); t6.reactorKilled = true; }
    if(t6.reactorKilled && t > 580 && t6.wallsAfter < 0) t6.wallsAfter = reactorWallHp();
    if(!t6.obeliskFired) Groups.build.each(function(b){ if(b.team == Team.sharded && b.block.name == "vg-obelisk" && b.bullets.size > 0) t6.obeliskFired = true; });
    turrets.forEach(function(b){ if(b != null && b.isValid() && b.block.name == "vg-requiem") mech.requiemHeat = Math.max(mech.requiemHeat || 0, b.heatReq); });
}
function t6Report(){
    mech.netIntercept = t6.netStats;
    mech.aegisSingular = { spawned: t6.aegisSpawned, passed: t6.aegisPassed, aegisBuildupMax: Math.round(t6.aegisMax) };
    mech.domeSingular = { spawned: t6.domeSpawned, leaked: t6.domeLeaked, jumps: t6.domeJumps };
    mech.reactor = { heat: Math.round(t6.reactorHeat), warmup: Math.round((t6.reactorWarmup || 0) * 100) / 100, wallsBefore: Math.round(t6.wallsBefore), wallsAfter: Math.round(t6.wallsAfter) };
    mech.obeliskFired = t6.obeliskFired;
    var g = t6.grav;
    mech.gravity = { valid: g != null && g.isValid(), item: (g != null && g.dominantItem != null) ? String(g.dominantItem.name) : "none", mined: g != null ? g.items.total() : 0 };
    var made = {};
    Groups.build.each(function(b){
        var n = String(b.block.name);
        if(n == "vg-seraphite-refinery") made.seraphimium = b.items.get(Vars.content.item("vg-seraphimium"));
        if(n == "vg-singularity-collider") made.singularCore = b.items.get(Vars.content.item("vg-singular-core"));
        if(n == "vg-antimatter-trap") made.antimatter = Math.round(b.liquids.get(Vars.content.liquid("vg-antimatter")));
    });
    mech.t6Crafted = made;
}

// ------------------------------------------------------------------ beta-1 labs (band x 8-110, y 196-232)
//  prospector drill on ferrolite floor ore; lance drill aimed (+x) at an iridite wall vein
//  heavy mass driver A -> B (60 tiles), A fed with copper; cargo hub fed with copper -> drone -> receiver set to copper
//  corrosion: a Lash next to a pinned dummy; T1-T3 generators and the vat/smelter by-products in the showcase
var b1 = { pros: null, lance: null, drvA: null, drvB: null, hub: null, recv: null, hubUnit: false, lashDummies: [] };
function layoutBetaLabs(){
    var fer = blk("vg-ore-ferrolite");
    for(var ox = 0; ox < 2; ox++) for(var oy = 0; oy < 2; oy++) Vars.world.tile(10 + ox, 200 + oy).setOverlay(fer);
    b1.pros = place(blk("vg-prospector-drill"), 10, 200, Team.sharded, 0);
    var wo = blk("vg-wall-ore-iridite");
    for(var wx = 25; wx < 28; wx++) for(var wy = 198; wy < 205; wy++){ var wt = Vars.world.tile(wx, wy); wt.setBlock(Blocks.stoneWall); wt.setOverlay(wo); }
    b1.lance = place(blk("vg-lance-drill"), 18, 200, Team.sharded, 0);
    b1.drvA = place(blk("vg-heavy-driver"), 36, 214, Team.sharded, 0);
    b1.drvB = place(blk("vg-heavy-driver"), 96, 214, Team.sharded, 0);
    if(b1.drvA != null && b1.drvB != null) b1.drvA.link = b1.drvB.pos();
    b1.hub = place(blk("vg-cargo-hub"), 40, 226, Team.sharded, 0);
    b1.recv = place(blk("vg-cargo-receiver"), 76, 226, Team.sharded, 0);
    if(b1.recv != null) b1.recv.item = Items.copper;
    place(blk("vg-lash"), 60, 198, Team.sharded, 1);
    dummy(62, 206, b1.lashDummies);
}
function betaUpdate(t){
    [b1.drvA, b1.hub].forEach(function(b){
        if(b == null || !b.isValid()) return;
        for(var n = 0; n < 20 && b.acceptItem(b, Items.copper); n++) b.handleItem(b, Items.copper);
    });
    if(b1.hub != null && b1.hub.isValid() && b1.hub.unit != null) b1.hubUnit = true;
    var st = statusByName("vg-corrosion"), nc = 0;
    if(st != null) b1.lashDummies.forEach(function(d){ if(d.u != null && d.u.hasEffect(st)) nc++; });
    mech.corrosionMax = Math.max(mech.corrosionMax || 0, nc);
}
function betaReport(){
    function items(b){ return (b != null && b.isValid()) ? b.items.total() : -1; }
    mech.prospector = { item: (b1.pros != null && b1.pros.dominantItem != null) ? String(b1.pros.dominantItem.name) : "none", mined: items(b1.pros) };
    mech.lance = { mined: items(b1.lance), iridite: (b1.lance != null) ? b1.lance.items.get(Vars.content.item("vg-iridite")) : -1 };
    mech.massDriver = { linked: b1.drvA != null && b1.drvA.link == b1.drvB.pos(), received: items(b1.drvB) };
    mech.cargo = { droneBuilt: b1.hubUnit, delivered: items(b1.recv) };
    var gen = {}, liq = {};
    Groups.build.each(function(b){
        var n = String(b.block.name);
        if(n == "vg-heat-engine" || n == "vg-hydrocarbon-plant") gen[n] = Math.round(b.productionEfficiency * 100) / 100;
        if(n == "vg-nanite-vat") liq.naniteSlurry = Math.round(b.liquids.get(Vars.content.liquid("vg-nanite-slurry")));
        if(n == "vg-steel-smelter") liq.moltenIron = Math.round(b.liquids.get(Vars.content.liquid("vg-molten-iron")));
    });
    mech.generators = gen;
    mech.byproducts = liq;
}

// ------------------------------------------------------------------ screenshots
function planShots(){
    var top = manifest.showcaseTop;
    addShot("00-showcase-overview", t0 + 60, SHOW_W / 2, top / 2, 0.6);
    var i = 1;
    for(var cy = 18; cy < top + 4; cy += 30){
        for(var cx = 30; cx < SHOW_W + 20; cx += 50){
            addShot("0" + (i++) + "-showcase-" + cx + "-" + cy, t0 + 70 + i * 4, cx, cy, 3);
        }
    }
    var rc = manifest.rangeEnd / 2;
    addShot("20-range-overview-a", t0 + 300, rc, 118, 0.9);
    addShot("25-mech-area", t0 + 560, MX + 185, 128, 1.6);
    addShot("26-tempest-lab", t0 + 620, 285, 40, 1.0);
    addShot("27-labs-shield-intercept", t0 + 660, 280, 178, 1.0);
    addShot("28-t6-labs-west", t0 + 300, 70, 300, 1.0);
    addShot("29-t6-labs-east", t0 + 330, 245, 292, 1.0);
    addShot("29b-dome-reactor-close", t0 + 534, 300, 299, 1.6);
    addShot("40-beta-labs", t0 + 345, 58, 214, 1.4);
    addShot("21-range-overview-b", t0 + 520, rc, 118, 0.9);
    for(var cx = 26, k = 0; cx < manifest.rangeEnd + 20; cx += 52, k++){
        addShot("3" + k + "-range-turrets-" + cx, t0 + 700 + k * 30, cx, 104, 2.6);
    }
    for(var f = 0; f < 36; f++){
        addShot("gif-" + (f < 10 ? "0" : "") + f, t0 + 900 + f * 5, rc, 112, 1.4, true);
    }
    shots.sort(function(a, b){ return a.at - b.at; });
}

function finish(){
    if(done) return;
    done = true;
    try{ mechReport(); }catch(e){ E("mechReport: " + e); }
    try{ OUT.child("manifest.json").writeString(JSON.stringify(manifest, null, 1)); }catch(e){ Log.err(e); }
    L("finished, errors: " + manifest.errors.length);
    Time.run(5, function(){ Core.app.exit(); });
}

Events.on(ClientLoadEvent, function(){
    OUT.mkdirs();
    Time.run(30, setup);
});

Events.run(Trigger.update, function(){
    if(t0 < 0 || done) return;
    try{
        if(++feedTick >= 15){ feedTick = 0; feed(); }
        mechUpdate();
        if(Time.time - t0 > 200 && ++waveTick >= 240){ waveTick = 0; spawnEnemies(); buildTargets(); }
        if(shotIdx >= shots.length){ finish(); return; }
        var s = shots[shotIdx];
        // the desktop input pulls the camera toward the player's unit every frame, so the player moves with the shot
        var sx = s.cx * 8, sy = s.cy * 8;
        Core.camera.position.set(sx, sy);
        try{
            Vars.player.set(sx, sy);
            var pu = Vars.player.unit();
            if(pu != null && pu.isValid()){ pu.set(sx, sy); pu.vel.setZero(); }
        }catch(e2){}
        Vars.renderer.setScale(s.scale);
        if(armedFrame < 0 && Time.time >= s.at) armedFrame = Core.graphics.getFrameId() + 2;
    }catch(e){ E("update: " + e); finish(); }
});

var polyPending = true;
Events.run(Trigger.postDraw, function(){
    // build plans for the rule test are added in the render phase (like player input), after the world settled
    if(polyPending && poly != null && Time.time - t0 > 120){ polyPending = false; poly.addBuild(new BuildPlan(130, 155, 0, Blocks.copperWall)); }
    if(armedFrame < 0 || done || Core.graphics.getFrameId() < armedFrame) return;
    var s = shots[shotIdx];
    // wait (up to 120 frames) until the camera has actually reached the shot target
    var camOff = Math.max(Math.abs(Core.camera.position.x - s.cx * 8), Math.abs(Core.camera.position.y - s.cy * 8));
    if(camOff > 12 && Core.graphics.getFrameId() < armedFrame + 120) return;
    try{
        ScreenUtils.saveScreenshot(OUT.child(s.name + ".png"));
        manifest.shots.push({ name: s.name, cx: s.cx, cy: s.cy, camX: Math.round(Core.camera.position.x / 8), camY: Math.round(Core.camera.position.y / 8), scale: s.scale, w: Core.graphics.getWidth(), h: Core.graphics.getHeight(), t: Time.time - t0 });
    }catch(e){ E("screenshot " + s.name + ": " + e); }
    shotIdx++;
    armedFrame = -1;
});
