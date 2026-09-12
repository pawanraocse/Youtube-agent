---
id: 20260912-asset-retention-c8de62
type: decision
subject: asset retention
created: 2026-09-12
source: developer decision 2026-09-12
---
Once an episode is PUBLISHED its per-shot stills, clips and chunk WAVs may be pruned; masters, verticals, thumbnails and all database rows are kept, since content addressing lets a pruned intermediate be regenerated at the same hash.
