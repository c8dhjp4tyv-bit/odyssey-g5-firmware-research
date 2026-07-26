# Recovered state machines

These diagrams contain only observed states/transitions. Dashed edges are
explicitly unresolved runtime, hardware, or cross-processor transitions.

## Boot and processor handoff

```mermaid
flowchart TD
    R0["8051 record 0 reset: 0000 -> 1360"] --> INIT["RAM/stack/flash initialization"]
    INIT --> PT["Read partition metadata"]
    PT -->|success flag RAM_20.2| LOAD["Load/start STBC and platform regions"]
    PT -.->|failure semantics unresolved| FAIL["Boot failure/retry path"]
    LOAD --> STBC["Record 1 reset at BACE"]
    STBC --> BRIDGE["PBus/AHB and Leon main/sub control"]
    BRIDGE --> TRAP["Record 3 SPARC trap/startup block"]
    TRAP --> MAIN["Main SPARC initialization and event tasks"]
    MAIN --> DISPLAY["Source/PQ/OSD operational state"]
    STBC -->|watchdog/system crash| RESET["Warm/system reset"]
    RESET --> R0
```

Evidence: record-0 reset `0000: ljmp 1360`, partition success return
`0x05A0`, STBC reset `0000: ljmp BACE`, Leon/PBus strings and reachable
calls, record-3 vector targets, main initialization anchors. The exact loader
relocation transaction for records 3/4/8 remains unresolved.

## USB firmware update

```mermaid
stateDiagram-v2
    [*] --> MediaScan
    MediaScan --> LoadToRAM: updater record 2 filesystem path
    LoadToRAM --> ModelVersionCheck: main 0x14CC9C
    ModelVersionCheck --> Reject: bad model/version/extension
    ModelVersionCheck --> WholeFileSum: accepted fixed format
    WholeFileSum --> Reject: sum16 mismatch
    WholeFileSum --> ConfirmOSD: valid
    ConfirmOSD --> ProgramRequest: user confirms
    ProgramRequest --> ISPController: mailbox/staging
    ISPController --> FlashRecords: 8051 ISP path
    FlashRecords --> ExternalType7: optional fwType == 7 only
    FlashRecords --> Reboot: normal completion
    ExternalType7 --> Reboot
    ISPController --> ErrorOSD: reported error
    ProgramRequest --> Percent1: asynchronous UI state
    Percent1 --> Reboot: hardware-observed after approximately one hour
    Percent1 --> ErrorOSD: transition condition unresolved
```

The displayed percentage is not proven to be a direct flash-address counter.
No UART/USB trace was captured during the observed one-hour 1% state.

## Input, long press, and OSD

```mermaid
flowchart LR
    ADC["STBC ADC/joystick"] --> RAW["raw key 1..5"]
    RAW --> MAP["raw-to-event table 0x2076B8"]
    MAP --> EVENT["SECAPP_KEYEVT 0x40..0x57"]
    EVENT --> LONG["state-dependent long-press mapper 0x17C2B8"]
    LONG --> KEYDISP["KeyActionDemander 0x17C4A4"]
    KEYDISP --> OSDDISP["processOsdEvent 0x17F078"]
    OSDDISP --> MENU["MenuHandler 0x1D6FE8"]
    MENU --> RENDER["normal/factory renderer"]
    LONG -->|UP -> MGA when state/flag match| MGA["synthetic event 0x54"]
    LONG -.->|runtime table replacement possible| ALT["unresolved alternate hardware path"]
```

Long-UP opening MGA is hardware-confirmed. The static `0x10` key-dispatch
cell does not alone explain that observation and is retained as an unresolved
alternate path.

## Source switching and signal acquisition

```mermaid
stateDiagram-v2
    [*] --> CableDetect
    CableDetect --> NoCable: absent
    CableDetect --> EDIDCapability: present
    EDIDCapability --> HPD
    HPD --> SyncAcquire
    SyncAcquire --> Unstable: lock not achieved
    SyncAcquire --> OutOfRange: timing rejected
    SyncAcquire --> TimingUpdate: valid
    TimingUpdate --> PQApply
    PQApply --> Display
    Unstable --> SyncAcquire
    OutOfRange --> OSDStatus
    NoCable --> OSDStatus
    Display --> CableDetect: source/cable event
```

Evidence anchors include `SecHalScaler_SetInputSource 0x1229F8`,
`ToggleHPD 0x11EBCC`, EDID read/write, sync callback `0x123620`, and
application cable/no-signal/unstable/out-of-range events. Exact per-port
debounce timers and every hardware interrupt edge remain unresolved.

## Power and DPMS

```mermaid
stateDiagram-v2
    [*] --> On
    On --> Saving: DPMS/no-signal policy
    Saving --> PanelOff: panel power/backlight sequence
    PanelOff --> Standby: STBC/Leon mailbox
    Standby --> Wake: key/cable/CEC event
    Wake --> PanelOn: clocks/bridge/panel sequence
    PanelOn --> On
    On --> PowerOff: physical/synthetic PWR event
    PowerOff --> Standby
    Standby --> ResetRecovery: watchdog/system crash
    ResetRecovery --> Wake
```

Main anchors: panel power `0x117A64`, backlight on/off
`0x117D64/0x117DE4`, DPMS handler `0x17B778`; STBC evidence includes ADC wake,
CEC power, Leon RUN/STOP, watchdog, and warm reset. GPIO numbers and exact
mailbox payload fields are unresolved.

## Factory/MGA

```mermaid
stateDiagram-v2
    [*] --> NormalOSD
    NormalOSD --> SyntheticMGA: long-UP and runtime condition
    SyntheticMGA --> FactoryRenderer: event 0x54
    FactoryRenderer --> NotSupported: descriptor supported == 0
    FactoryRenderer --> MGAList: descriptor supported == 1
    MGAList --> Render35: walk 35 descriptors
    Render35 --> ReadOnlyZero: kind 2/3
    Render35 --> GenericByteEditor: kind 4 only
    GenericByteEditor --> WrongPersistentSelector: forced MGA mutation
    WrongPersistentSelector --> [*]: unsafe; not released
    MGAList --> NormalOSD: Back to upper
```

The released change affects only `supported`; it does not change dispatcher,
item kinds, storage, or apply logic.

## Error recovery

```mermaid
flowchart TD
    E1["PBus/AHB error"] --> RESET["watchdog/system reset"]
    E2["USB checksum/model/version failure"] --> UPDATEERR["update error OSD"]
    E3["sync unstable/out-of-range"] --> SIGNAL["signal-status OSD and reacquire"]
    E4["flash/ISP failure"] -.-> UNKNOWN["cross-processor retry/abort unresolved"]
    RESET --> BOOT["boot state machine"]
    UPDATEERR --> IDLE["normal UI"]
    SIGNAL --> ACQUIRE["source acquisition"]
    UNKNOWN -.-> BOOT
    UNKNOWN -.-> IDLE
```

No claim is made that these diagrams recover every source-level state variable.
They are the complete set of currently evidenced high-level machines; missing
edges are explicitly marked rather than inferred.
