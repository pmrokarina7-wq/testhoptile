#!/usr/bin/env bash
# Packs mod/ into build/ and loads it in a headless Mindustry v146 server.
# Usage: [VG_BUILD=build/x] tools/loadtest.sh [extra server commands...]   (log: $VG_BUILD/server.log)
set -euo pipefail
cd "$(dirname "$0")/.."
jar="$PWD/.cache/mindustry/server-release.jar"
[ -s "$jar" ] || tools/setup-env.sh

version=$(sed -n 's/^version: *"\(.*\)"/\1/p' mod/mod.hjson)
B=${VG_BUILD:-build}
mkdir -p "$B"
zip="$B/vanguard-arsenal-$version.zip"
rm -f "$zip"
(cd mod && zip -q -r -X "../$zip" .)

srv=$B/server
rm -rf "$srv" && mkdir -p "$srv/config/mods"
cp "$zip" "$srv/config/mods/"

{
  sleep 25
  for c in "$@"; do echo "$c"; sleep 3; done
  echo exit
} | (cd "$srv" && timeout 180 java -jar "$jar" 2>&1) | sed 's/\x1b\[[0-9;]*m//g' > "$B/server.log" || true

ls -la "$zip"
echo "--- errors/warnings:"
grep -nE '\[E\]|\[W\]|Exception|rror' "$B/server.log" | head -100 || true
echo "--- mods:"
grep -nE 'Loaded|mods? loaded|content' "$B/server.log" | head -20 || true
