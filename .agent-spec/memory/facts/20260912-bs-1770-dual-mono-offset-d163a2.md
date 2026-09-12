---
id: 20260912-bs-1770-dual-mono-offset-d163a2
type: constraint
subject: BS.1770 dual-mono offset
created: 2026-09-12
source: SESSION-SNAPSHOT 2026-09-12
---
Any mono-compatibility check must subtract 10*log10(channels) before thresholding: BS.1770 sums channel power, so a conforming dual-mono master measures exactly 3.01 LU louder than its own fold-down. Counting that artefact as phase cancellation made LOCK 3 impossible to open (DEBT-003).
