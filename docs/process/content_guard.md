# Public-Scope Content Guard

The public-scope content guard is implemented in
`scripts/check_public_scope_terms.py`.

It scans public Markdown, HTML, JSON, YAML, XML, TXT, and CFF files for phrases
that often indicate prohibited certification, structural-use, jobsite,
consumer, or public mains/control-panel claims.

The guard is warning-only by default. It exits successfully unless run with
`--strict`. This allows the repository to document boundary language while the
cleanup is still in progress. After owner/legal/electrical review, selected
phrases can be promoted to blocking failures.

## Local use

```powershell
py scripts/check_public_scope_terms.py
py scripts/check_public_scope_terms.py --strict
```

## Approved contexts

The guard allows explicit safety/boundary documents and process/audit records to
use otherwise risky terms when the context is warning, prohibition, supersession,
or review policy. It should still be reviewed manually; a warning-free scan is
not professional sign-off.
