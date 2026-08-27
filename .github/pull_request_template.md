## Summary

Describe the change and the evidence it adds or updates.

## Provenance

For firmware-address, patch, or hardware claims, include:

- exact monitor model and panel revision, if known
- firmware filename, size, SHA-256, and complete-file `sum16`
- VA and file offset
- original bytes and interpretation
- how the path was reached
- static, emulator, and hardware confidence separately

## Safety

- [ ] No Samsung firmware, extracted proprietary payload, manual, or IDA database containing firmware bytes is included.
- [ ] Cross-model or cross-revision offsets are not presented as validated without independent evidence.
- [ ] Feature-enabling changes identify the reachable handler and verified hardware path.
- [ ] Any mutating change documents the exact minimal diff, checksum/version consequences, and recovery assumptions.
- [ ] Unresolved semantics are labeled as unresolved rather than presented as confirmed.

## Validation

List the commands run and, when applicable, hardware observations. For repository changes, the expected baseline is:

```bash
python3 -m unittest discover -s tests -v
python3 -O -m unittest discover -s tests -v
```

For generated-analysis changes, also state whether checked-in artifacts regenerate byte-identically.
