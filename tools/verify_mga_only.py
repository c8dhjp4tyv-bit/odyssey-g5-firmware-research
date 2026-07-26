#!/usr/bin/env python3
"""Verify a generated MGA-only image against the exact stock firmware."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path

from build_mga_only import (
    DATA_CHECKSUM_PLACEHOLDER,
    EXPECTED_OUTPUT_SHA256,
    EXPECTED_OUTPUT_SUM16,
    EXPECTED_SIZE,
    EXPECTED_SOURCE_SHA256,
    EXPECTED_SOURCE_SUM16,
    KEY_DISPATCH_FILE,
    MGA_SUPPORT_FILE,
    NEW_VERSION,
    PICTURE_SHARED_FILE,
    VERSION_FILE,
    require,
    sum16,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock_image", type=Path)
    parser.add_argument("generated_image", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.stock_image.read_bytes()
    generated = args.generated_image.read_bytes()

    require(
        len(source) == EXPECTED_SIZE,
        "unexpected stock firmware size",
    )
    require(
        len(generated) == EXPECTED_SIZE,
        "unexpected generated firmware size",
    )
    require(
        sha256(source).hexdigest() == EXPECTED_SOURCE_SHA256,
        "stock firmware SHA-256 mismatch",
    )
    require(
        sum16(source) == EXPECTED_SOURCE_SUM16,
        "stock firmware complete-file sum16 mismatch",
    )
    require(
        sha256(generated).hexdigest() == EXPECTED_OUTPUT_SHA256,
        "generated firmware SHA-256 mismatch",
    )
    require(
        sum16(generated) == EXPECTED_OUTPUT_SUM16,
        "generated firmware complete-file sum16 mismatch",
    )

    diffs = [
        offset
        for offset, (before, after) in enumerate(zip(source, generated))
        if before != after
    ]
    require(
        diffs == [VERSION_FILE + 3, MGA_SUPPORT_FILE],
        "generated image does not have the exact expected two-byte diff",
    )
    require(
        generated[
            VERSION_FILE : VERSION_FILE + len(NEW_VERSION)
        ] == NEW_VERSION,
        "generated image embedded version mismatch",
    )
    require(
        generated[MGA_SUPPORT_FILE] == 1,
        "generated image MGA support byte mismatch",
    )
    require(
        generated[PICTURE_SHARED_FILE] == 0,
        "generated image changed the shared Factory Picture byte",
    )
    require(
        generated[KEY_DISPATCH_FILE] == source[KEY_DISPATCH_FILE] == 0x10,
        "generated image changed the key-dispatch byte",
    )
    require(
        generated[
            DATA_CHECKSUM_PLACEHOLDER : DATA_CHECKSUM_PLACEHOLDER + 4
        ] == source[
            DATA_CHECKSUM_PLACEHOLDER : DATA_CHECKSUM_PLACEHOLDER + 4
        ] == b"\xFF\xFF\xFF\xFF",
        "generated image changed the data checksum placeholder",
    )

    print("verification=PASS")
    print(f"sha256={sha256(generated).hexdigest()}")
    print(f"sum16=0x{sum16(generated):04X}")
    print("exact_two_byte_diff=PASS")
    print("picture_shared_condition_stock=PASS")
    print("key_dispatch_unchanged=PASS")


if __name__ == "__main__":
    main()
