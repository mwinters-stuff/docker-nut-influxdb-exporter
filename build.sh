#!/bin/bash
BRANCH=$1
git clone --depth=1 --single-branch --branch ${BRANCH} https://github.com/mihai-cindea/nut-influxdb-exporter.git || exit 1
cd nut-influxdb-exporter || exit 1

VER=$(TZ="utc" date -Iseconds)
echo "date_version=${VER}"