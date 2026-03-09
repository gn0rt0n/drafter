---
created: 2026-03-09T17:04:25.175Z
title: Split schema.md into multiple files
area: docs
files:
  - docs/schema.md
---

## Problem

`docs/schema.md` documents all 71+ database tables across 14 domains in a single file. At this scale it's too large to navigate, review, or update without scrolling through unrelated sections.

## Solution

Split into one file per domain (e.g. `docs/schema/characters.md`, `docs/schema/world.md`, etc.) mirroring the migration domain groupings, with an index at `docs/schema.md` or `docs/schema/README.md` that links to each domain file.
