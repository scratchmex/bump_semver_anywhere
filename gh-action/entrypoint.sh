#!/bin/sh

# configure gh-action identity in git
git config --global user.name "github-actions[bot]"
git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"

exec python -m manver $*