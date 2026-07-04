---
description: Initialize this repo (or empty directory) as a Project Steward managed project — survey, interview, then generate AGENTS.md + CLAUDE.md + .project-steward/ with approval gates.
---

Follow the **project-init** skill end to end: detect existing state
(including legacy .projectforge/), run the read-only survey
(`project-steward survey --json` if available), interview the user about
load-bearing unknowns only, show the full AGENTS.md draft for approval,
apply via `project-steward init ... --yes`, then offer git init/commit.
$ARGUMENTS
