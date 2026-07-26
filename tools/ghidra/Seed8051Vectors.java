// Seed raw 8051 reset/interrupt vectors before headless autoanalysis.
// @category OdysseyG5

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;

public class Seed8051Vectors extends GhidraScript {
    private boolean isVectorOpcode(int opcode) {
        return opcode == 0x02 || opcode == 0x32 || (opcode & 0x1f) == 0x01;
    }

    private void seed(long offset) throws Exception {
        Address address = currentProgram.getAddressFactory()
            .getDefaultAddressSpace().getAddress(offset);
        new DisassembleCommand(address, null, true).applyTo(currentProgram, monitor);
        new CreateFunctionCmd(address).applyTo(currentProgram, monitor);
    }

    @Override
    public void run() throws Exception {
        seed(0);
        for (long offset = 3; offset < 0x84; offset += 8) {
            Address address = currentProgram.getAddressFactory()
                .getDefaultAddressSpace().getAddress(offset);
            if (!currentProgram.getMemory().contains(address)) {
                continue;
            }
            int opcode = currentProgram.getMemory().getByte(address) & 0xff;
            if (isVectorOpcode(opcode)) {
                seed(offset);
            }
        }
    }
}
