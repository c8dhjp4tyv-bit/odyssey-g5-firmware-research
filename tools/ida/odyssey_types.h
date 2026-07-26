#pragma pack(push, 1)

typedef unsigned char  u8;
typedef unsigned short u16;
typedef unsigned int   u32;

typedef struct {
    u32 flash_target_be;
    u32 payload_length_be;
    u32 checksum_or_sentinel_be;
    u32 record_tag_be;
    u8  reserved[16];
} nvtsc_record_header_t;

typedef struct {
    u32 trap_id_be;
    u32 string_pointer_be;
} trap_name_entry_t;

typedef struct {
    char name[0x18];
    u32 kind_be;
    u32 display_format_be;
    u32 maximum_be;
    u16 primary_selector_be;
    u16 secondary_selector_be;
    u32 apply_selector_be;
} factory_item_descriptor_t;

typedef enum {
    SECAPP_KEYEVT_PWR = 0x40,
    SECAPP_KEYEVT_MENU = 0x41,
    SECAPP_KEYEVT_AUTO = 0x42,
    SECAPP_KEYEVT_INPUT = 0x43,
    SECAPP_KEYEVT_FUNC = 0x44,
    SECAPP_KEYEVT_UP = 0x45,
    SECAPP_KEYEVT_DOWN = 0x46,
    SECAPP_KEYEVT_LEFT = 0x47,
    SECAPP_KEYEVT_RIGHT = 0x48,
    SECAPP_KEYEVT_FACT = 0x4D,
    SECAPP_KEYEVT_FACTRESET = 0x4E,
    SECAPP_KEYEVT_MGA = 0x54,
    SECAPP_KEYEVT_TESTPAT = 0x55,
    SECAPP_KEYEVT_NONE = 0x56,
    SECAPP_KEYEVT_END = 0x57
} secapp_key_event_t;

#pragma pack(pop)
