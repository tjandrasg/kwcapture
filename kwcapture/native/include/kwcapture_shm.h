/* Shared-memory protocol between kwcapture (daemon) and its clients.
 *
 * The daemon mmaps a file (default $XDG_RUNTIME_DIR/kwcapture.shm), grabs frames
 * straight out of KWin into a ring slot, then publishes by releasing frame_seq.
 * A client mmaps the same file read-only and asks for a frame by bumping req_seq;
 * it then spins until frame_seq >= the number it requested.  No locks, no copies.
 *
 * Frame N lives in slot ((N-1) % slots) at offset hdr_size + slot*slot_bytes.
 *
 * SPDX-License-Identifier: MIT
 */
#ifndef KWCAPTURE_SHM_H
#define KWCAPTURE_SHM_H

#include <stdint.h>

#define KWC_MAGIC 0x4B574350u /* "KWCP" */
#define KWC_MAGIC_GONE 0x4B574347u /* "KWCG" - daemon shut down */
#define KWC_VERSION 2u /* v2: per-frame status + window target */
#define KWC_MAX_SLOTS 8u

/* What the daemon was asked to capture. */
#define KWC_TARGET_ACTIVE_SCREEN 0u
#define KWC_TARGET_SCREEN 1u
#define KWC_TARGET_AREA 2u
#define KWC_TARGET_WORKSPACE 3u
#define KWC_TARGET_WINDOW 4u
#define KWC_TARGET_ACTIVE_WINDOW 5u

/* Per-frame status.  A grab can fail *after* the client asked for it - the classic case
 * is a window capture whose window got closed.  The frame is still published (with no
 * pixels and status != 0) so the ring keeps flowing instead of wedging; the client
 * translates the code into an exception.  Values >= 4096 are KWin screenshot errors,
 * anything else is an errno. */
#define KWC_OK 0u
#define KWC_ERR_INVALID_WINDOW 4096u   /* window is gone (closed) */
#define KWC_ERR_NO_ACTIVE_WINDOW 4097u /* nothing focused */
#define KWC_ERR_CANCELLED 4098u
#define KWC_ERR_NOT_AUTHORIZED 4099u
#define KWC_ERR_INVALID_SCREEN 4100u
#define KWC_ERR_INVALID_AREA 4101u
#define KWC_ERR_EMPTY_FRAME 4102u /* KWin answered OK with a 0x0 image: nothing to show */

typedef struct {
    uint32_t width, height, stride, format; /* format: QImage::Format (6 = ARGB32 premul = BGRA) */
    double scale;
    double grab_ms;  /* compositor time: call -> reply */
    double total_ms; /* call -> last pixel received */
    uint64_t ts_ns;  /* CLOCK_MONOTONIC at publish */
    char screen[64];
    uint32_t status; /* KWC_OK, KWC_ERR_* or an errno; geometry is zeroed if not OK */
    uint32_t pad[7];
} kwc_slot_t;

typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t hdr_size;   /* offset of pixel data from the start of this struct */
    uint32_t slot_bytes; /* bytes per frame slot */
    uint32_t slots;      /* ring slots */

    /* --- handshake / lifecycle ------------------------------------------- */
    volatile uint32_t ready;   /* daemon up, first frame published */
    volatile uint32_t quit;    /* client asks daemon to exit */
    volatile uint32_t error;   /* errno-ish, set on fatal errors */
    uint32_t daemon_pid;
    uint32_t capture_pid; /* unused, reserved */
    uint32_t pad2[2];     /* keep the u64s 8-byte aligned at a fixed offset */

    /* --- frame sync ------------------------------------------------------ */
    volatile uint64_t req_seq;   /* client: deliver frame number req_seq */
    volatile uint64_t frame_seq; /* daemon: frame number frame_seq is complete */
    volatile uint64_t published; /* total frames published */

    /* --- latest geometry (also per slot) -------------------------------- */
    uint32_t width, height, stride, format;
    double scale;
    char screen[64];

    /* --- tuning the daemon was started with ----------------------------- */
    uint32_t depth;
    uint32_t pad3;
    double fps;

    /* --- what we are capturing (window support, v2) ---------------------- */
    uint32_t target; /* KWC_TARGET_* */
    uint32_t pad4;
    char window[64]; /* window handle (QUuid string) for window captures, else empty */

    kwc_slot_t slot[KWC_MAX_SLOTS];

    uint8_t reserved[512];
} kwc_hdr_t;

/* If you change the layout above, update this number AND the mirror in
 * kwcapture.py (_KWC_STRUCT_SIZE).  Both sides assert on it. */
#define KWC_HDR_STRUCT_SIZE 1912u
#if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L
_Static_assert(sizeof(kwc_hdr_t) == KWC_HDR_STRUCT_SIZE,
               "kwc_hdr_t layout changed: update KWC_HDR_STRUCT_SIZE and kwcapture.py");
#endif

#endif /* KWCAPTURE_SHM_H */
