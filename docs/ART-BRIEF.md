# Art rework brief (shared by all art workstreams)

Repository: /tmp/hoplite/workspace (git). Project: **Vanguard Arsenal**, a JSON+JS content mod for **Mindustry v146** (PC + Android, no Java), themed on Supreme Commander 2 factions. Docs: `docs/VANGUARD-TZ.md` (spec, see §2.5 "Переделка моделей до уровня «Скорпиона»"), `docs/vanguard-arsenal-plan.md` (roles, factions, numbers), `docs/TESTING.md`.

## Goal
Raise the listed assets to the "Scorpion / hero" quality level that the owner approved. The owner's verdict on the current versions of these assets: "халтурно" (sloppy). Flat recoloured boxes are rejected outright. The owner judges by eye on comparison sheets.

## The pipeline (do not replace it — the owner approved its look)
- `tools/art/` is a small numpy 3D pipeline: you build a low-poly 3D model in Python (triangles grouped by layer name, each with a material), and `rend.render_layer` renders it **orthographic top-down at 32 px per tile** with one directional light + ambient, shadow map, AO, edge darkening, then posterises every material to its own 6-step palette ramp. Sprites must look like Mindustry pixel art at game scale.
- Coordinates: 1.0 = one tile, Z up, origin = block centre, turret heads face **+Y**.
- Read these first: `tools/art/geom.py` (primitives: prism, loft, cyl, box, cbox, tube_path, cham_rect, mirror_half, rz/rx/ry, tf …), `tools/art/mats.py` (Model, material list), `tools/art/rend.py` (renderer, palette RAMPS, `add_material`), `tools/art/hero.py` (the hero detail kit: slope_plate with inlays, buttress legs, turntable, grille, coil_jacket, hydraulic, muzzle_brake, cable, shell, antenna, seam, uef_hero_base, cy_hero_base, heat_grad), `tools/art/export.py` (exporters that write straight into `mod/sprites/...`: `turret()`, `layer()`, `save()`, `outline()`, `heat_sprite()`, `over()`, `liquid_fill()`, `glowfn`, `matfn`, `qa_sheet()`).
- Hero-level examples to study and match: `tools/art/models5.py` (howl5, redoubt5, mantis5) and `tools/art/models6.py` (monolith6, bastion6, suppressor6, citadel6, cryocondenser, iridium_smelter, sc_chamber, plasma_heater, fusion_reactor, items). Their sprites are in `mod/sprites` (e.g. `blocks/turrets/scorpion-full.png`, `mantis-full.png`, `monolith-full.png`, `blocks/defense/citadel.png`, `blocks/power/fusion-reactor.png`). Previews: `/tmp/va/vanguard-arsenal-full/03-previews/hero-compare.png`, `t4-contact.png`, `stage3-contact.png`.
- The current (to be replaced) sprites are snapshotted in `build/art-before/` (same tree as `mod/sprites`).

## Quality requirements (from the TZ + owner)
- A separate, purpose-built 3D model per asset: stepped armour plates with chamfers, panel seams, hatches, bolts, vents/grilles, cables/pipes, glowing nodes, readable mechanisms (pistons, crucibles, coils, rotors…). Budget: turrets ~6–12k triangles, industry/defence ~4–8k, walls/items less. `Model.ntri()` gives the count.
- Readability at 32 px/tile matters more than triangle count: strong silhouette, clear light/dark separation of top vs side faces, no large single-tone fills, detail that reads as shapes, not noise. View your output at 1:1 and x3.
- Faction palettes: **UEF** = blocky blue-grey steel (`hull_*`, `steel`, `metal*`) with **yellow** trim (`yellow`) and blue glow (`glow`); **Cybran** = angular black/dark (`cy_dark`, `cy_mid`, `hull_dark`) with **red** armour (`red_armor`) and red/white glow (`rglow`). Industry uses its resource colours as accents (see RAMPS: `alu`, `cobalt`, `tung`, `magnet`, `chlor`, `flame`, `copper`…). Determine each asset's faction from the plan/bundles and the current sprite.
- Heat/glow layers follow the geometry (barrels, coils, nozzles, crucibles), never a red copy of the silhouette.
- Turret icon must look like the assembled turret (the `-full` sprite = base + body + parts).
- Keep in-game behaviour: same sprite **file names** and **canvas sizes** as now (check them in `build/art-before`), because content JSON references them; animated layers (spinner, rotator, piston, top1/top2, glow, heat, team, cell, leg, base) must still line up and animate correctly. You may change a canvas size or add/remove layers **only** if you also update the owning block/unit JSON in `mod/content/...` and that JSON is in your assigned list.
- New materials: call `rend.add_material(name, [6 hex colours dark→light], glow=False)` at the top of **your own** module (append-only; never edit the shared RAMPS).

## Your files (strict)
- Write your models + render driver in ONE new module `tools/art/<your module>.py` (name given in your task). Running `.venv/bin/python tools/art/<your module>.py` must regenerate all your assets into `mod/sprites` deterministically, and print triangle counts.
- You may overwrite only your assets' sprites under `mod/sprites/` and edit only the content JSON files listed in your task.
- Do NOT edit shared files: `tools/art/{geom,mats,rend,hero,export,compare,models,models5,models6,verify_pipeline}.py`, `tools/*.sh`, `tools/harness/**`, `mod/scripts/**`, `mod/bundles/**`, `mod/mod.hjson`, `docs/**`, or anything belonging to other workstreams. If you believe a shared change is needed, describe it in your report instead.
- Do NOT run git commit/push/checkout/stash/reset or anything that changes git state. The coordinator commits.

## Verification you must do
1. Render, then **look at your sprites** with the Read tool (PNG files). Iterate on the models at least twice until each asset is clearly at the Scorpion/T4 level. Be self-critical: compare side by side with `scorpion-full.png`, `mantis-full.png`, `citadel.png`, `fusion-reactor.png`.
2. Comparison sheets: `.venv/bin/python tools/art/compare.py <asset names…>` → `build/art/compare/<name>-compare.png` (Scorpion | before | after | after x3). Make one per asset and view them.
3. Load test in the real game server (isolated build dir): `VG_BUILD=build/<your module> tools/loadtest.sh` — must print `1 mods loaded` and no `[E]`/`[W]` lines.
4. In-game check (real v146 client, software GL, takes ~30 s): `VG_BUILD=build/<your module> VG_DISPLAY=<your display> CLIENT_TIMEOUT=240 tools/clienttest.sh`. Screenshots land in `build/<your module>/shots/` (`01..0N-showcase-*.png` show every block at x3 zoom on a grid, `3*-range-turrets-*.png` show the turret firing line, `gif-*.png` frames of the battle, `manifest.json` has block positions). Find your assets there and confirm they render at the right size/orientation with layers aligned. Other workstreams are editing other sprites at the same time — ignore their assets.

## Report (your final message)
- Per asset: what the model contains (key features), triangle count, layers produced, any canvas/JSON change (with the exact JSON edits).
- Paths of comparison sheets and 1–2 in-game screenshots that show your assets.
- Load test result line(s) and any in-game problems seen.
- Anything you could not finish, and any shared-file change you think is needed.
