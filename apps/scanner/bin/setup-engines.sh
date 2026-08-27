#!/usr/bin/env bash
# Install the external scanning engines that vg-scan aggregates.
#
# No sudo and no system packages: everything lands in .engines/ next to the
# scanner, so it can be wiped and rebuilt and a VPS gets the identical set.
#
#   ./bin/setup-engines.sh
#
# Re-running is safe; it updates in place.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENGINES="$HERE/.engines"
BIN="$ENGINES/bin"
mkdir -p "$BIN"

NUCLEI_VERSION="${NUCLEI_VERSION:-3.11.1}"
WEBANALYZE_VERSION="${WEBANALYZE_VERSION:-0.4.3}"
TESTSSL_IMAGE="${TESTSSL_IMAGE:-drwetter/testssl.sh:3.2}"

say() { printf '\n== %s\n' "$1"; }

# --- testssl.sh -------------------------------------------------------------
# GPLv2. The reference tool for TLS configuration and the known TLS
# vulnerabilities (ROBOT, Heartbleed, POODLE, LUCKY13, BEAST, ...).
#
# Run from the official image rather than a local clone. testssl.sh 3.2 has a
# WSL-only bug - an unquoted NXCONNECT assignment makes bash try to execute
# "127.0.0.1:0" - and a pinned container behaves here exactly as on the VPS.
say "testssl.sh (docker image)"
if command -v docker >/dev/null 2>&1; then
  docker pull -q "$TESTSSL_IMAGE" >/dev/null 2>&1 && echo "pulled $TESTSSL_IMAGE"
else
  echo "docker not found - the testssl engine will report itself unavailable"
fi

# --- nuclei -----------------------------------------------------------------
# MIT. Template-driven detection. We only ever run the passive template subsets
# selected in engines/nuclei.py, never the intrusive ones.
say "nuclei $NUCLEI_VERSION"
if [ ! -x "$BIN/nuclei" ]; then
  tmp="$(mktemp -d)"
  curl -sSL --max-time 300 -o "$tmp/nuclei.zip" \
    "https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip"
  ( cd "$tmp" && unzip -qo nuclei.zip nuclei )
  mv "$tmp/nuclei" "$BIN/nuclei"
  chmod +x "$BIN/nuclei"
  rm -rf "$tmp"
fi
"$BIN/nuclei" -version 2>&1 | tail -1

say "nuclei templates"
"$BIN/nuclei" -update-templates -silent >/dev/null 2>&1 || true
TEMPLATES="${HOME}/nuclei-templates"
if [ -d "$TEMPLATES" ]; then
  printf 'templates: %s (%s files)\n' "$TEMPLATES" "$(find "$TEMPLATES" -name '*.yaml' | wc -l)"
else
  echo "templates: MISSING"
fi

# --- webanalyze -------------------------------------------------------------
# MIT. Wappalyzer-style fingerprints: CMS, plugins, frameworks, analytics, often
# with versions. Wappalyzer itself went commercial; this is the maintained fork.
# Note: release assets carry no version in the filename.
say "webanalyze $WEBANALYZE_VERSION"
if [ ! -x "$BIN/webanalyze" ]; then
  tmp="$(mktemp -d)"
  curl -sSL --max-time 300 -o "$tmp/wa.tar.gz" \
    "https://github.com/rverton/webanalyze/releases/download/v${WEBANALYZE_VERSION}/webanalyze_Linux_x86_64.tar.gz"
  tar -xzf "$tmp/wa.tar.gz" -C "$tmp"
  mv "$tmp/webanalyze" "$BIN/webanalyze"
  chmod +x "$BIN/webanalyze"
  rm -rf "$tmp"
fi
( cd "$ENGINES" && "$BIN/webanalyze" -update >/dev/null 2>&1 || true )

say "installed"
ls -1 "$BIN"
if [ -f "$ENGINES/technologies.json" ]; then
  printf 'technologies.json: present (%s bytes)\n' "$(stat -c%s "$ENGINES/technologies.json")"
else
  echo "technologies.json: MISSING"
fi
if command -v docker >/dev/null 2>&1 && docker image inspect "$TESTSSL_IMAGE" >/dev/null 2>&1; then
  echo "testssl image:     $TESTSSL_IMAGE"
fi
