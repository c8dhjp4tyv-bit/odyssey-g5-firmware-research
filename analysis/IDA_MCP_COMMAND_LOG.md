# IDA MCP analysis-command ledger

This is the repository-visible command ledger for the connected IDA session
`main_deep_complete`. It records analysis-affecting/read-only queries used for
published conclusions. It is not a server transport audit log.

| Tool | Arguments | Purpose/result |
|---|---|---|
| `survey_binary` | database `main_deep_complete`, standard | 3,074 IDA functions; 16,762 strings; segment/statistics survey |
| `disasm` | `0x1B5CE4`, 35 instructions | demonstrated callable entries at `1B5CE4`, `1B5CF8`, `1B5D0C` inside one IDA container |
| `disasm` | `0x127854`, 80 instructions | identified formatter/UART service path |
| `disasm` | `0x1A4EF8` | callback slot `0xA8037D84` indirect invocation |
| `disasm` | `0x17A8FC` | callback registration routine and callback constants |
| `xref_query` | to `0x129D64`, `0x129E54`, `0x12A074`, `0x12A734`, `0x1588B0` | LDC setup/update reachability |
| `xref_query` | to `0x158AFC`, `0x158C34`, `0x159570` | distinguished unreachable setup from reachable gain helper |
| `xref_query` | to `0x172F5C`, `0x172F44`, `0x172F0C` | recovered normal initialization callers |
| `analyze_function` | `0x172F5C` with assembly | intensity-mode wrapper behavior |
| `analyze_function` | `0x158C34` with assembly | common gain-array update behavior |
| `analyze_function` | `0x114D14` with assembly | normal initialization reachability |

Bulk inventories were exported read-only through
[`export_ida_inventory.py`](../tools/export_ida_inventory.py). The repository
does not distribute IDBs or firmware bytes.
