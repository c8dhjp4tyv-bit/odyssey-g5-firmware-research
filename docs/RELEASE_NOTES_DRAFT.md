# Draft release notes: v1.0.1

This is a repository-hardening and research-metadata release. It does **not** distribute Samsung firmware and does not change the documented two-byte MGA-only firmware patch.

## Repository hardening

- Add `SECURITY.md` with safety-sensitive reporting guidance.
- Add structured hardware-validation and firmware-research issue forms.
- Add a pull-request checklist aligned with the project's evidence hierarchy.
- Add Dependabot updates for GitHub Actions.
- Pin GitHub Actions to verified commit SHAs while retaining the corresponding `v7` comments.
- Add `CITATION.cff` so research users can cite the repository and exact revision used.
- Add a CI status badge to the README.

## Firmware scope remains unchanged

Validated target:

```text
Model:     LS32CG552EUXUF
Base:      M-C5500GGZA-1010.0[D43B].img
Base SHA:  2e901cf2677b688d740dc62b279faedbee991c726ab5c3dcf75d156115cc96e7
Output:    M-C5500GGZA-1014.0[D440].img
Output SHA: 815f28e8e1eaba498c07cd500d581c63b16a887ea0da274152d1297b8d237350
```

The final firmware diff remains exactly:

```text
0x273367: 30 -> 34   embedded version 1010.0 -> 1014.0
0x2D2776: 00 -> 01   MGA category supported byte
```

No firmware image is included in this repository or release.

## Suggested GitHub release title

`v1.0.1 — repository hardening and citation metadata`
