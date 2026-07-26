"""IDA loader for owner-supplied Odyssey G5 NVTSC images.

Offers separate analysis views for the known executable regions. Companion
records with unknown runtime relocation are intentionally not invented.
"""

import ida_idp
import ida_loader
import ida_segment

MAGIC = b"\x7fNVTSC_IMG\n"
FORMATS = (
    (
        "Odyssey main SPARC",
        "sparcb",
        (
            ("CODE", "CODE", 0x12E000, 0x100000, 0xEFCE0, True),
            ("DATA", "DATA", 0x21DD00, 0x1F0000, 0xFB9C0, False),
        ),
    ),
    ("Odyssey link SPARC", "sparcb", (("CODE", "CODE", 0x3196E0, 0xA0060000, 0x2FB00, True),)),
    ("Odyssey trap SPARC (probable base)", "sparcb", (("CODE", "CODE", 0x23CE0, 0xA00E0000, 0x7760, True),)),
    ("Odyssey boot 8051", "8051", (("CODE", "CODE", 0x40, 0x0000, 0x8000, True),)),
    ("Odyssey STBC 8051", "8051", (("CODE", "CODE", 0x8060, 0x0000, 0xFAC0, True),)),
    ("Odyssey updater 8051", "8051", (("CODE", "CODE", 0x17B40, 0x0000, 0xC180, True),)),
)


def accept_file(li, index):
    li.seek(0)
    if li.read(len(MAGIC)) != MAGIC or index >= len(FORMATS):
        return 0
    name, processor, _regions = FORMATS[index]
    return {"format": name, "processor": processor}


def load_file(li, neflags, format_name):
    selected = next((item for item in FORMATS if item[0] == format_name), None)
    if selected is None:
        return 0
    _name, processor, regions = selected
    ida_idp.set_processor_type(processor, ida_idp.SETPROC_LOADER)
    for seg_name, seg_class, file_offset, base, length, executable in regions:
        segment = ida_segment.segment_t()
        segment.start_ea = base
        segment.end_ea = base + length
        segment.bitness = 1
        segment.perm = ida_segment.SEGPERM_READ
        if executable:
            segment.perm |= ida_segment.SEGPERM_EXEC
        else:
            segment.perm |= ida_segment.SEGPERM_WRITE
        ida_segment.add_segm_ex(
            segment,
            seg_name,
            seg_class,
            ida_segment.ADDSEG_NOSREG | ida_segment.ADDSEG_OR_DIE,
        )
        ida_loader.file2base(li, file_offset, base, base + length, True)
    return 1
