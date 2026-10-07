#!/bin/sh

set -e

if [ $# -eq 0 ]; then
    echo "Please supply a CalVer version (e.g. 2026-10-6)."
    exit
fi

git switch main
git pull

uv version "$1"

$EDITOR sketch_map_tool/__init__.py

pytest

git add -p pyproject.toml sketch_map_tool/__init__.py
git add uv.lock

git commit -m "Release $1"
git push

git tag "$1" -m "$1"
git push origin "$1"

# Create a GitHub release
#
# Manually start the Jenkins build for the new release tag at https://jenkins.heigit.org/job/OQAPI/view/tags/ 
