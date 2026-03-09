---
created: 2026-03-09T17:04:25.175Z
title: Split mcp-tools.md into multiple files
area: docs
files:
  - docs/mcp-tools.md
---

## Problem

`docs/mcp-tools.md` documents all 103 MCP tools across 14 domains in a single file. At this scale it's unwieldy to navigate, edit, or review. The file likely mirrors the domain structure already used in `src/novel/tools/`.

## Solution

Split into one file per domain (e.g. `docs/tools/characters.md`, `docs/tools/gate.md`, etc.) with an index file at `docs/mcp-tools.md` or `docs/tools/README.md` that links to each domain file.
