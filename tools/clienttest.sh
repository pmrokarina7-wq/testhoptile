#!/usr/bin/env bash
# Runs the real Mindustry v146 desktop client (Xvfb + Mesa llvmpipe) with the mod and the test stand.
# Output: $VG_BUILD/shots/*.png, shots/manifest.json, client.log (VG_BUILD defaults to build, VG_DISPLAY to :99)
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD
jar="$PWD/.cache/mindustry/Mindustry.jar"
[ -s "$jar" ] || curl -fsSL -o "$jar" https://github.com/Anuken/Mindustry/releases/download/v146/Mindustry.jar

M=${VG_MOD:-mod}
version=$(sed -n 's/^version: *"\(.*\)"/\1/p' "$M/mod.hjson")
B=${VG_BUILD:-build}
D=${VG_DISPLAY:-:99}
mkdir -p "$B"
zip="$B/vanguard-arsenal-$version.zip"
rm -f "$zip" "$B/vgtest.zip"
(cd "$M" && zip -q -r -X "$ROOT/$zip" .)
(cd "${VG_HARNESS:-tools/harness}" && zip -q -r -X "$ROOT/$B/vgtest.zip" .)

data=$PWD/$B/client-data
rm -rf "$data" "$B/shots" && mkdir -p "$data/Mindustry/mods" "$B/shots"
cp "$zip" "$data/Mindustry/mods/"
cp "$B/vgtest.zip" "$data/Mindustry/mods/"

pgrep -f "Xvfb $D " >/dev/null || { Xvfb $D -screen 0 1280x800x24 >/dev/null 2>&1 & sleep 2; }
DISPLAY=$D XDG_DATA_HOME="$data" timeout "${CLIENT_TIMEOUT:-300}" java -jar "$jar" 2>&1 \
  | grep -v '^ALSA lib\|^Jack\|jack server\|Cannot connect to server' | sed 's/\x1b\[[0-9;]*m//g' > "$B/client.log" || true

cp -r "$data/Mindustry/vgtest/." "$B/shots/" 2>/dev/null || true
echo "--- log (errors / vg lines):"
grep -nE '\[E\]|\[W\]|\[vg|Exception' "$B/client.log" | grep -v 'community servers\|Failed to initialize audio' | head -60 || true
echo "--- shots: $(ls "$B"/shots/*.png 2>/dev/null | wc -l)"
