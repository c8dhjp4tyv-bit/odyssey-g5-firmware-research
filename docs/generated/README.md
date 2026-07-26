# Generated analysis catalogs

These CSV files are derived metadata. They contain no Samsung firmware bytes.

| File | Rows | Meaning |
|---|---:|---|
| `main_functions.csv` | 3,074 | IDA-discovered functions in the main SPARC image |
| `main_symbol_anchors.csv` | 250 | Function-name inferences backed by debug-string xrefs |
| `aux_functions.csv` | 565 | IDA-discovered functions in the separate link/EQ SPARC image |
| `aux_symbol_anchors.csv` | 22 | Named HDMI/DP functions backed by string xrefs |
| `boot8051_functions.csv` | 46 | Conservatively defined functions in the 8051 boot partition |

`direct_categories` are keyword classifications from strings referenced
inside the function. `graph_inferred_categories` are lower-confidence labels
propagated from at least two neighboring labeled functions when one category
held at least 60% of the votes. An empty graph label means no inference was
made. These labels are navigation aids, not recovered source-level types.

IDA can merge function tails or miss indirect calls in stripped SPARC code.
The address and byte bounds are useful, but instruction/call counts should be
treated as analysis-tool observations rather than ground truth.
