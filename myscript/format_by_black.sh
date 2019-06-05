#!/usr/bin/env bash
black . -l 120 --exclude "/(\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|_build|buck-out|build|dist|myscript|sent2vec_wrapper)/"
