#!/usr/bin/env bash
# Local toolchain: Java + Mindustry v146 server jar (load tests), Python deps for the art generators.
set -euo pipefail
cd "$(dirname "$0")/.."

# java: server and client; xvfb + mesa: the desktop client in tools/clienttest.sh renders through llvmpipe; zip: packing
need=""
command -v java >/dev/null || need="$need openjdk-17-jre-headless"
command -v Xvfb >/dev/null || need="$need xvfb"
dpkg -s libgl1-mesa-dri >/dev/null 2>&1 || need="$need libgl1-mesa-dri libglx-mesa0"
command -v zip >/dev/null || need="$need zip unzip"
if [ -n "$need" ]; then
  apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $need >/dev/null
fi

mkdir -p .cache/mindustry
jar=.cache/mindustry/server-release.jar
[ -s "$jar" ] || curl -fsSL -o "$jar" https://github.com/Anuken/Mindustry/releases/download/v146/server-release.jar

[ -d .venv ] || uv venv -q .venv
uv pip install -q --python .venv/bin/python numpy pillow

java -version 2>&1 | head -1
ls -la "$jar"
.venv/bin/python -c "import numpy, PIL; print('numpy', numpy.__version__, 'pillow', PIL.__version__)"
