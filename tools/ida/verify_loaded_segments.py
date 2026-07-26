"""Batch smoke test for the custom IDA loader."""

import ida_ida
import ida_pro
import ida_segment

if ida_segment.get_segm_qty() < 1:
    print("ODYSSEY_IDA_LOADER_SMOKE=FAIL:no-segment")
    ida_pro.qexit(1)

segment = ida_segment.getnseg(0)
print(
    "ODYSSEY_IDA_LOADER_SMOKE=PASS "
    f"processor={ida_ida.inf_get_procname()} "
    f"start=0x{segment.start_ea:X} end=0x{segment.end_ea:X}"
)
ida_pro.qexit(0)
