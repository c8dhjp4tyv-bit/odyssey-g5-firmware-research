#!/usr/bin/env python3
"""Build the verified MGA-only Odyssey G5 G55C LS32CG552EUXUF image.

The Samsung firmware itself is not distributed. The user must provide the
exact owner-supplied M-C5500GGZA-1010.0[D43B].img identified by
EXPECTED_SOURCE_SHA256. It is called the base image because official Samsung
provenance has not been independently established.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path


EXPECTED_SIZE = 3_449_760
EXPECTED_SOURCE_SHA256 = (
    "2e901cf2677b688d740dc62b279faedbee991c726ab5c3dcf75d156115cc96e7"
)
EXPECTED_SOURCE_SUM16 = 0xD43B
EXPECTED_OUTPUT_SHA256 = (
    "815f28e8e1eaba498c07cd500d581c63b16a887ea0da274152d1297b8d237350"
)
EXPECTED_OUTPUT_SUM16 = 0xD440

VERSION_FILE = 0x273364
OLD_VERSION = b"1010.0"
NEW_VERSION = b"1014.0"
MGA_SUPPORT_FILE = 0x2D2776
PICTURE_SHARED_FILE = 0x2D278D
KEY_DISPATCH_FILE = 0x2354BC
DATA_CHECKSUM_PLACEHOLDER = 0x21DCE8
OUTPUT_NAME = "M-C5500GGZA-1014.0[D440].img"


def sum16(data: bytes | bytearray) -> int:
    return sum(data) & 0xFFFF


def require(condition: bool, message: str) -> None:
    """Reject an unsafe input even when Python runs with optimization."""
    if not condition:
        raise SystemExit(f"ERROR: {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_image", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="output directory (default: ./output)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.base_image.read_bytes()

    require(len(source) == EXPECTED_SIZE, "unexpected firmware size")
    require(
        sha256(source).hexdigest() == EXPECTED_SOURCE_SHA256,
        "source SHA-256 mismatch; refusing to patch a different firmware",
    )
    require(
        sum16(source) == EXPECTED_SOURCE_SUM16,
        "source complete-file sum16 mismatch",
    )
    require(
        source[VERSION_FILE : VERSION_FILE + len(OLD_VERSION)] == OLD_VERSION,
        "embedded source version mismatch",
    )
    require(
        source[MGA_SUPPORT_FILE] == 0,
        "MGA support byte is not the expected base value",
    )
    require(
        source[PICTURE_SHARED_FILE] == 0,
        "shared Factory Picture byte is not the expected base value",
    )
    require(
        source[KEY_DISPATCH_FILE] == 0x10,
        "key-dispatch byte is not the expected base value",
    )
    require(
        source[
            DATA_CHECKSUM_PLACEHOLDER : DATA_CHECKSUM_PLACEHOLDER + 4
        ] == b"\xFF\xFF\xFF\xFF",
        "data checksum placeholder is not the expected base value",
    )

    output = bytearray(source)
    output[VERSION_FILE : VERSION_FILE + len(NEW_VERSION)] = NEW_VERSION
    output[MGA_SUPPORT_FILE] = 1

    diffs = [
        offset
        for offset, (before, after) in enumerate(zip(source, output))
        if before != after
    ]
    require(
        diffs == [VERSION_FILE + 3, MGA_SUPPORT_FILE],
        "generated image does not have the exact expected two-byte diff",
    )
    require(
        output[PICTURE_SHARED_FILE] == 0,
        "generated image changed the shared Factory Picture byte",
    )
    require(
        sum16(output) == EXPECTED_OUTPUT_SUM16,
        "generated image complete-file sum16 mismatch",
    )
    require(
        sha256(output).hexdigest() == EXPECTED_OUTPUT_SHA256,
        "generated image SHA-256 mismatch",
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / OUTPUT_NAME
    destination.write_bytes(output)

    print(f"output={destination}")
    print(f"size={len(output)}")
    print(f"sha256={sha256(output).hexdigest()}")
    print(f"sum16=0x{sum16(output):04X}")
    print("diffs=" + ",".join(f"0x{offset:X}" for offset in diffs))


if __name__ == "__main__":
    main()
