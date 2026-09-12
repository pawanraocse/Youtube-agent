---
id: 20260912-resume-rule-eac908
type: decision
subject: resume rule
created: 2026-09-12
source: SESSION-SNAPSHOT 2026-09-12
---
A pipeline step is skipped if and only if a steps row exists with a matching input_hash and status='ok'; every new stage must go through Store.step or it is not resumable.
