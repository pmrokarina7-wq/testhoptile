// Vanguard Arsenal in-game test stand (NOT shipped with the mod).
// Builds a test world with every vg block, a firing range and mechanic labs, takes screenshots from the
// real renderer, measures the JS/engine mechanics and exits. Output: <data>/vgtest/*.png + manifest.json
var OUT = Core.settings.getDataDirectory().child("vgtest");
var W = 330, H = 240, SHOW_W = 232;
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
        var k = Math.floor(t / 45) % 2;
        if(k == 0) qiSpawn("redoubt-T2", "vg-redoubt", "vg-charge", 201);
        else qiSpawn("tempest-T5", "vg-tempest", "vg-iridium", 203);
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
}

function mechReport(){
    mech.polyPlans = poly.plans.size;
    mech.polyBuilt = String(Vars.world.tile(130, 155).block().name);
    mech.engPlans = eng.plans.size;
    mech.engBuilt = String(Vars.world.tile(134, 155).block().name);
    mech.shieldJumps = shield.jumps;
    mech.intercept = qi.stats;
    delete mech.mantis; delete mech.monolith;
    manifest.mech = mech;
    L("mech " + JSON.stringify(mech));
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
        Core.camera.position.set(s.cx * 8, s.cy * 8);
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
    try{
        ScreenUtils.saveScreenshot(OUT.child(s.name + ".png"));
        manifest.shots.push({ name: s.name, cx: s.cx, cy: s.cy, scale: s.scale, w: Core.graphics.getWidth(), h: Core.graphics.getHeight(), t: Time.time - t0 });
    }catch(e){ E("screenshot " + s.name + ": " + e); }
    shotIdx++;
    armedFrame = -1;
});
