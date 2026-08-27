# Security policy

This repository documents owner-performed firmware research on a specific Samsung Odyssey G5 G55C monitor revision. Treat any firmware modification, updater behavior, recovery path, or factory-service finding as safety-sensitive until independently validated.

## Reporting a security-sensitive finding

If a finding could plausibly cause persistent device damage, bypass a model/panel safety gate, expose a destructive update path, or enable unsafe factory writes, do not publish a ready-to-flash image or proprietary firmware payload in an issue.

Report the minimum reproducible evidence instead:

- exact monitor model and panel revision, if known
- firmware filename, size, SHA-256, and complete-file `sum16`
- exact file offset and virtual address when applicable
- original bytes and proposed bytes
- how the path was reached
- whether the result is static-only, emulator-observed, or hardware-observed
- recovery assumptions and known failure modes

If GitHub private vulnerability reporting is available for this repository, prefer that for findings that would be unsafe to disclose before review. Otherwise open a minimal issue that omits proprietary payloads and clearly mark the report as safety-sensitive.

## Do not upload proprietary firmware

Do not attach Samsung firmware images, extracted proprietary payloads, manuals, IDA databases containing firmware bytes, or dumps copied from another device. Hashes, offsets, independently written analysis, scripts, and small non-copyrightable metadata are preferred.

## Scope

The released modification is pinned to the exact base image and hardware target documented in `README.md`. A finding is not considered portable to another firmware revision, model suffix, panel revision, or screen size unless separately validated.

## Release bar

Security-sensitive or feature-enabling changes must satisfy the evidence hierarchy in `SAFETY.md` and the acceptance criteria in `CONTRIBUTING.md`. In particular, strings or dormant descriptors alone are not enough to call an action usable.
