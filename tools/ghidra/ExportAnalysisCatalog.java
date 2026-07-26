// Export the deterministic part of Ghidra's function analysis.
//
// Ghidra's parallel auto-analysis may produce scheduler-dependent function
// bodies, switch labels, and call edges for this stripped firmware.  Function
// entry addresses were stable across clean-project repetitions, so the public
// cross-tool artifact deliberately records only that reproducible evidence.
// @category OdysseyG5

import java.io.BufferedWriter;
import java.io.FileWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class ExportAnalysisCatalog extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("expected output CSV path");
        }
        try (BufferedWriter out = new BufferedWriter(new FileWriter(args[0]))) {
            out.write("address\n");
            FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext() && !monitor.isCancelled()) {
                Function function = functions.next();
                out.write(String.format("0x%08x\n", function.getEntryPoint().getOffset()));
            }
        }
        println("Exported deterministic function-start catalog to " + args[0]);
    }
}
