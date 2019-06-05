#!/usr/bin/env bash
find . -name "0*.py" | grep migrations | xargs rm
find . -name "*.pyc" | grep migrations | xargs rm
git ls-files -d | xargs git checkout --
