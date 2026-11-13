#!/usr/bin/env bash
# Bundle the Three.js landing scene (src/scene) into js/landing.bundle.js (IIFE, works from file://).
set -e
cd "$(dirname "$0")/../src"
[ -d node_modules ] || npm install --no-audit --no-fund
npx esbuild scene/entry.js --bundle --minify --format=iife --target=es2019 --outfile=../js/landing.bundle.js
