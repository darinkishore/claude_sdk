#!/usr/bin/env bash
set -euo pipefail
fixtures_dir=$(cd "$(dirname "$0")/../fixtures" && pwd)
source_file="$fixtures_dir/example_sample.jsonl"
dest_dir="$fixtures_dir/transitions"
mkdir -p "$dest_dir"
head -n 1 "$source_file" > "$dest_dir/before_example.jsonl"
head -n 2 "$source_file" > "$dest_dir/after_example.jsonl"
