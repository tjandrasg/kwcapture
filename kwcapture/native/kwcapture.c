/* kwcapture - fast screen capture on KDE Plasma (KWin Wayland)
 *
 * Why this exists: on Wayland there is no root-window to read from.  KWin exposes
 * org.kde.KWin.ScreenShot2 over D-Bus, which writes raw ARGB32-premultiplied pixels
 * (== BGRA on little endian) into a file descriptor we hand it.  KWin authorises a
 * caller only if /proc/<pid>/exe matches a .desktop file declaring
 * X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2 -- so this has to be a
 * native binary with its own desktop file (kwcapture.desktop), not a Python script.
 * See AGENTS.md for the full investigation.
 *
 * Modes
 *   kwcapture [opts]              grab one frame -> --out FILE (default stdout)
 *   kwcapture --bench N [opts]    timing loop
 *   kwcapture --list              list outputs (Wayland registry)
 *   kwcapture --list-windows      list capturable windows (KWin window handles)
 *   kwcapture serve [opts]        resident daemon publishing frames into shared memory
 *
 * Targets: active screen (default), --screen NAME, --area X,Y,W,H, --workspace,
 * --window <handle> (see --list-windows) and --active-window.

 * KWin sends the D-Bus reply *before* the pixel data has been written (it writes the
 * fd from a thread pool), so EOF on the pipe - not the reply - is the frame boundary.
 *
 * SPDX-License-Identifier: MIT
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include <systemd/sd-bus.h>
#include <wayland-client.h>

#include "kwcapture_shm.h"

#define SVC "org.kde.KWin.ScreenShot2"
#define OBJ "/org/kde/KWin/ScreenShot2"
#define IFACE "org.kde.KWin.ScreenShot2"
#define NIFL 8 /* in-flight request tracking entries */

/* one captured frame, as reported by KWin */
typedef struct {
    uint32_t width, height, stride, format;
    double scale;
    uint64_t ts_ns;
    char screen[64];
    char window[64]; /* KWin reports "windowId" for window captures */
} frame_out_t;

static volatile sig_atomic_t g_sig = 0;
static void on_signal(int s)
{
    g_sig = s;
}

static uint64_t now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}
static double ms_between(uint64_t a, uint64_t b)
{
    return (double)(b - a) / 1e6;
}

static void die(const char *msg, int err)
{
    fprintf(stderr, "kwcapture: %s: %s\n", msg, strerror(err > 0 ? err : -err));
    exit(1);
}

/* --------------------------------------------------------------- options */
typedef struct {
    const char *screen; /* NULL -> active screen */
    int area[4];        /* x, y, w, h */
    int use_area, use_workspace;
    const char *window; /* window handle (QUuid string) from --list-windows */
    int active_window;
    int include_decoration, include_shadow, include_cursor, native_resolution;
    int hide_caller_windows;
} opts_t;

static int opts_target(const opts_t *o)
{
    if (o->active_window)
        return KWC_TARGET_ACTIVE_WINDOW;
    if (o->window)
        return KWC_TARGET_WINDOW;
    if (o->use_area)
        return KWC_TARGET_AREA;
    if (o->use_workspace)
        return KWC_TARGET_WORKSPACE;
    if (o->screen)
        return KWC_TARGET_SCREEN;
    return KWC_TARGET_ACTIVE_SCREEN;
}

static void build_call(sd_bus *bus, const opts_t *o, sd_bus_message **out)
{
    const char *member;
    if (o->active_window)
        member = "CaptureActiveWindow";
    else if (o->window)
        member = "CaptureWindow";
    else if (o->use_area)
        member = "CaptureArea";
    else if (o->use_workspace)
        member = "CaptureWorkspace";
    else if (o->screen)
        member = "CaptureScreen";
    else
        member = "CaptureActiveScreen";

    if (sd_bus_message_new_method_call(bus, out, SVC, OBJ, IFACE, member) < 0)
        die("out of memory", ENOMEM);
    if (o->active_window) {
        /* no arguments besides options + pipe */
    } else if (o->window)
        sd_bus_message_append(*out, "s", o->window);
    else if (o->use_area)
        sd_bus_message_append(*out, "iiuu", o->area[0], o->area[1], (uint32_t)o->area[2],
                              (uint32_t)o->area[3]);
    else if (!strcmp(member, "CaptureScreen"))
        sd_bus_message_append(*out, "s", o->screen);

    sd_bus_message_open_container(*out, 'a', "{sv}");
    struct { const char *k; int v; } kv[] = {
        {"include-decoration", o->include_decoration},
        {"include-shadow", o->include_shadow},
        {"include-cursor", o->include_cursor},
        {"native-resolution", o->native_resolution},
        {"hide-caller-windows", o->hide_caller_windows},
    };
    for (unsigned i = 0; i < sizeof(kv) / sizeof(kv[0]); i++) {
        sd_bus_message_open_container(*out, 'e', "sv");
        sd_bus_message_append(*out, "s", kv[i].k);
        sd_bus_message_append(*out, "v", "b", kv[i].v ? 1 : 0);
        sd_bus_message_close_container(*out);
    }
    sd_bus_message_close_container(*out);
    /* caller appends the 'h' (write end of our pipe) */
}

/* --------------------------------------------------------- reply metadata */
typedef struct {
    uint32_t width, height, stride, format;
    double scale;
    char screen[64];
    char window[64];
} meta_t;

static void parse_results(sd_bus_message *reply, meta_t *m)
{
    m->screen[0] = '\0';
    m->window[0] = '\0';
    if (sd_bus_message_enter_container(reply, 'a', "{sv}") < 0)
        return;
    while (sd_bus_message_enter_container(reply, 'e', "sv") > 0) {
        const char *key = NULL;
        sd_bus_message_read(reply, "s", &key);
        sd_bus_message_enter_container(reply, 'v', NULL);
        char type = 0;
        const char *contents = NULL;
        sd_bus_message_peek_type(reply, &type, &contents);
        if (type == 'u' || type == 't') {
            uint64_t v = 0;
            sd_bus_message_read_basic(reply, type, &v);
            if (!strcmp(key, "width"))
                m->width = (uint32_t)v;
            else if (!strcmp(key, "height"))
                m->height = (uint32_t)v;
            else if (!strcmp(key, "stride"))
                m->stride = (uint32_t)v;
            else if (!strcmp(key, "format"))
                m->format = (uint32_t)v;
        } else if (type == 'd') {
            double d = 0;
            sd_bus_message_read_basic(reply, 'd', &d);
            if (!strcmp(key, "scale"))
                m->scale = d;
        } else if (type == 's') {
            const char *s = NULL;
            sd_bus_message_read_basic(reply, 's', &s);
            if (!strcmp(key, "screen") && s)
                snprintf(m->screen, sizeof(m->screen), "%s", s);
            else if (!strcmp(key, "windowId") && s)
                snprintf(m->window, sizeof(m->window), "%s", s);
        } else {
            sd_bus_message_skip(reply, NULL);
        }
        sd_bus_message_exit_container(reply);
        sd_bus_message_exit_container(reply);
    }
    sd_bus_message_exit_container(reply);
}

/* ================================================================ one shot
 * Blocking grab: reply gives the geometry, then we drain the pipe to EOF.
 * Returns the pixel buffer (grown as needed) and timings in *f.
 */
static int grab_sync(sd_bus *bus, const opts_t *o, uint8_t **buf, size_t *cap, frame_out_t *f,
                     double *grab_ms, double *read_ms)
{
    sd_bus_error error = SD_BUS_ERROR_NULL;
    sd_bus_message *call = NULL, *reply = NULL;
    int fds[2], r;

    if (pipe2(fds, O_CLOEXEC) < 0)
        return -errno;

    build_call(bus, o, &call);
    sd_bus_message_append(call, "h", fds[1]);

    uint64_t t0 = now_ns();
    r = sd_bus_call(bus, call, 0, &error, &reply);
    uint64_t t1 = now_ns();
    close(fds[1]);
    if (r < 0) {
        fprintf(stderr, "kwcapture: %s\n", error.message ? error.message : "D-Bus call failed");
        sd_bus_error_free(&error);
        sd_bus_message_unref(call);
        close(fds[0]);
        return r;
    }

    meta_t m = {0};
    parse_results(reply, &m);
    size_t want = (size_t)m.stride * m.height;
    if (want == 0) {
        fprintf(stderr, "kwcapture: KWin returned bogus geometry (%ux%u stride %u)\n", m.width,
                m.height, m.stride);
        sd_bus_message_unref(reply);
        sd_bus_message_unref(call);
        close(fds[0]);
        return -EIO;
    }
    if (!*buf || *cap < want) {
        free(*buf);
        *cap = (want + 4095) & ~(size_t)4095;
        *buf = aligned_alloc(64, *cap);
        if (!*buf) {
            sd_bus_message_unref(reply);
            sd_bus_message_unref(call);
            close(fds[0]);
            return -ENOMEM;
        }
    }
    size_t got = 0;
    r = 0;
    while (got < want) {
        ssize_t n = read(fds[0], *buf + got, want - got);
        if (n == 0)
            break;
        if (n < 0) {
            if (errno == EINTR)
                continue;
            r = -errno;
            break;
        }
        got += (size_t)n;
    }
    uint64_t t2 = now_ns();
    close(fds[0]);
    sd_bus_message_unref(reply);
    sd_bus_message_unref(call);
    if (r < 0)
        return r;
    if (got != want) {
        fprintf(stderr, "kwcapture: short read: %zu of %zu bytes\n", got, want);
        return -EIO;
    }

    f->width = m.width;
    f->height = m.height;
    f->stride = m.stride;
    f->format = m.format;
    f->scale = m.scale;
    f->ts_ns = t2;
    snprintf(f->screen, sizeof(f->screen), "%s", m.screen);
    snprintf(f->window, sizeof(f->window), "%s", m.window);
    *grab_ms = ms_between(t0, t1);
    *read_ms = ms_between(t1, t2);
    return 0;
}

/* =================================================================== serve */
/* Map a KWin screenshot D-Bus error name onto a slot status code. */
static uint32_t kwc_status_for_dbus_error(const char *name)
{
    if (!name)
        return KWC_ERR_CANCELLED;
    if (strstr(name, "InvalidWindow"))
        return KWC_ERR_INVALID_WINDOW;
    if (strstr(name, "NoActiveWindow"))
        return KWC_ERR_NO_ACTIVE_WINDOW;
    if (strstr(name, "NoAuthorized"))
        return KWC_ERR_NOT_AUTHORIZED;
    if (strstr(name, "InvalidScreen"))
        return KWC_ERR_INVALID_SCREEN;
    if (strstr(name, "InvalidArea"))
        return KWC_ERR_INVALID_AREA;
    if (strstr(name, "Cancelled"))
        return KWC_ERR_CANCELLED;
    return KWC_ERR_CANCELLED;
}

typedef struct {
    int active; /* dispatched and not finished */
    int done;   /* finished (pixels in shared memory, or failed), waiting to be published */
    uint32_t status; /* KWC_OK, or the frame is empty and carries this error */
    uint64_t seq;
    int read_fd;
    size_t want, got, shm_off;
    meta_t meta;
    uint64_t sent_ns, replied_ns;
} inflight_t;

typedef struct {
    sd_bus *bus;
    const opts_t *o;
    kwc_hdr_t *h;
    uint8_t *pixels;
    size_t slot_bytes;
    uint32_t slots;
    int depth;
    inflight_t ifl[NIFL];
    uint64_t dispatched; /* highest frame number handed to KWin */
    uint64_t next_due_ns;
    uint64_t frame_interval_ns;
    uint64_t last_activity_ns;
    uint64_t idle_exit_ns;
    int req_fd;   /* FIFO read end: clients poke us instead of us polling blindly */
    char req_path[512];
} server_t;

static inflight_t *ifl_entry(server_t *s, uint64_t seq)
{
    return &s->ifl[(seq - 1) % NIFL];
}

static int grab_callback(sd_bus_message *m, void *userdata, sd_bus_error *ret_error)
{
    inflight_t *in = userdata;
    if (ret_error && ret_error->name) {
        fprintf(stderr, "kwcapture: grab %llu failed: %s\n", (unsigned long long)in->seq,
                ret_error->message ? ret_error->message : ret_error->name);
        if (in->read_fd >= 0) {
            close(in->read_fd);
            in->read_fd = -1;
        }
        /* Publish the frame anyway, with status set: a window that got closed must not
         * wedge the ring (clients turn the status into an exception). */
        in->active = 0;
        in->want = in->got = 0;
        in->status = kwc_status_for_dbus_error(ret_error->name);
        in->replied_ns = now_ns();
        in->done = 1;
        return 0;
    }
    in->status = KWC_OK;
    parse_results(m, &in->meta);
    in->want = (size_t)in->meta.stride * in->meta.height;
    in->replied_ns = now_ns();
    if (in->meta.width == 0 || in->meta.height == 0 || in->want == 0) {
        /* KWin answers *successfully* with a 0x0 image when the target has nothing to
         * show: a closed, unmapped or minimised window (its scene item is hidden, so
         * visibleGeometry() is empty).  Nothing to drain -- report a failed frame
         * instead of waiting forever for pixels that will never arrive. */
        fprintf(stderr,
                "kwcapture: grab %llu: the compositor returned an empty frame "
                "(%ux%u stride %u)\n",
                (unsigned long long)in->seq, in->meta.width, in->meta.height,
                in->meta.stride);
        if (in->read_fd >= 0) {
            close(in->read_fd);
            in->read_fd = -1;
        }
        in->active = 0;
        in->want = in->got = 0;
        in->status = KWC_ERR_EMPTY_FRAME;
        in->done = 1;
    }
    return 0;
}

static int inflight_count(server_t *s)
{
    int n = 0;
    for (int i = 0; i < NIFL; i++)
        n += s->ifl[i].active;
    return n;
}

static int dispatch(server_t *s)
{
    uint64_t seq = s->dispatched + 1;
    inflight_t *in = ifl_entry(s, seq);
    if (in->active || in->done)
        return -EBUSY; /* ring full: client is behind */

    int fds[2];
    if (pipe2(fds, O_CLOEXEC | O_NONBLOCK) < 0)
        return -errno;
    sd_bus_message *call = NULL;
    build_call(s->bus, s->o, &call);
    sd_bus_message_append(call, "h", fds[1]);

    in->seq = seq;
    in->read_fd = fds[0];
    in->want = in->got = 0;
    in->done = 0;
    in->active = 1;
    in->sent_ns = now_ns();
    in->shm_off = (size_t)((seq - 1) % s->slots) * s->slot_bytes;

    int r = sd_bus_call_async(s->bus, NULL, call, grab_callback, in, 0);
    sd_bus_message_unref(call);
    close(fds[1]);
    if (r < 0) {
        fprintf(stderr, "kwcapture: sd_bus_call_async: %s\n", strerror(-r));
        in->active = 0;
        close(in->read_fd);
        in->read_fd = -1;
        return r;
    }
    s->dispatched = seq;
    return 0;
}

/* Publish every frame whose data is complete, in order. */
static void advance(server_t *s)
{
    kwc_hdr_t *h = s->h;
    for (;;) {
        uint64_t cur = __atomic_load_n(&h->frame_seq, __ATOMIC_ACQUIRE);
        inflight_t *in = ifl_entry(s, cur + 1);
        if (!in->done)
            break;
        uint64_t sloti = (cur) % s->slots; /* frame cur+1 -> slot (cur+1-1)%slots */
        kwc_slot_t *sl = &h->slot[sloti];
        sl->status = in->status;
        /* a failed frame has no pixels: report zero geometry so nobody reads the stale
         * contents of the slot by accident */
        sl->width = in->status ? 0 : in->meta.width;
        sl->height = in->status ? 0 : in->meta.height;
        sl->stride = in->status ? 0 : in->meta.stride;
        sl->format = in->meta.format;
        sl->scale = in->meta.scale;
        sl->grab_ms = ms_between(in->sent_ns, in->replied_ns);
        sl->total_ms = ms_between(in->sent_ns, now_ns());
        sl->ts_ns = now_ns();
        snprintf(sl->screen, sizeof(sl->screen), "%s", in->meta.screen);
        __atomic_store_n(&h->width, sl->width, __ATOMIC_RELEASE);
        __atomic_store_n(&h->height, sl->height, __ATOMIC_RELEASE);
        __atomic_store_n(&h->stride, sl->stride, __ATOMIC_RELEASE);
        __atomic_store_n(&h->format, in->meta.format, __ATOMIC_RELEASE);
        h->scale = in->meta.scale; /* ordered by the frame_seq release below */
        h->screen[0] = '\0';
        if (in->meta.screen[0])
            snprintf(h->screen, sizeof(h->screen), "%s", in->meta.screen);
        if (in->meta.window[0])
            snprintf(h->window, sizeof(h->window), "%s", in->meta.window);

        in->active = 0;
        in->done = 0;
        __atomic_store_n(&h->published, cur + 1, __ATOMIC_RELEASE);
        __atomic_store_n(&h->frame_seq, cur + 1, __ATOMIC_RELEASE);
        s->last_activity_ns = now_ns();
    }
}

/* Non-blocking drain of one in-flight pipe into its ring slot. */
static void drain(server_t *s, inflight_t *in)
{
    if (!in->active || !in->want)
        return; /* reply not parsed yet */
    if (in->want > s->slot_bytes) {
        fprintf(stderr, "kwcapture: frame needs %zu bytes, slot has %zu -- restart with a bigger ring\n",
                in->want, s->slot_bytes);
        __atomic_store_n(&s->h->error, ENOSPC, __ATOMIC_RELEASE);
        __atomic_store_n(&s->h->quit, 1, __ATOMIC_RELEASE);
        return;
    }
    uint8_t *dst = s->pixels + in->shm_off;
    int eof = 0;
    while (in->got < in->want) {
        ssize_t n = read(in->read_fd, dst + in->got, in->want - in->got);
        if (n > 0) {
            in->got += (size_t)n;
            continue;
        }
        if (n < 0 && errno == EINTR)
            continue;
        if (n == 0)
            eof = 1;
        break; /* EAGAIN (try again later) or EOF */
    }
    if (in->got >= in->want || eof) {
        if (eof && in->got < in->want) {
            /* KWin closed the pipe early (cancelled?); don't stall the ring. */
            fprintf(stderr, "kwcapture: frame %llu: got %zu of %zu bytes before EOF\n",
                    (unsigned long long)in->seq, in->got, in->want);
            in->status = EIO; /* the slot contents are incomplete: do not hand them out */
        }
        close(in->read_fd);
        in->read_fd = -1;
        in->done = 1;
        advance(s);
    }
}

static int mode_serve(const opts_t *o, const char *shm_path, uint32_t slots, int depth,
                      double fps, double idle_exit_s)
{
    server_t s = {0};
    s.o = o;
    s.slots = slots;
    s.depth = depth;
    s.frame_interval_ns = fps > 0 ? (uint64_t)(1e9 / fps) : 0;
    s.idle_exit_ns = idle_exit_s > 0 ? (uint64_t)(idle_exit_s * 1e9) : 0;
    for (int i = 0; i < NIFL; i++)
        s.ifl[i].read_fd = -1;

    int fd = open(shm_path, O_RDWR | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
    if (fd < 0)
        die(shm_path, errno);

    /* Request channel: a FIFO next to the ring.  Clients write one byte to wake us;
     * we open it O_RDWR so we never see EOF and never block. */
    snprintf(s.req_path, sizeof(s.req_path), "%s.req", shm_path);
    unlink(s.req_path);
    if (mkfifo(s.req_path, 0600) < 0 && errno != EEXIST)
        die(s.req_path, errno);
    s.req_fd = open(s.req_path, O_RDWR | O_NONBLOCK | O_CLOEXEC);
    if (s.req_fd < 0)
        die("open request fifo", errno);

    sd_bus_open_user(&s.bus);

    /* One blocking grab first: learns the geometry so we can size the ring, and
     * gives clients a usable frame the instant they attach. */
    uint8_t *tmp = NULL;
    size_t tmpcap = 0;
    frame_out_t f = {0};
    double gms, rms;
    int r = grab_sync(s.bus, o, &tmp, &tmpcap, &f, &gms, &rms);
    if (r < 0)
        die("initial grab failed", r);

    size_t need = (size_t)f.stride * f.height;
    /* Round up so a hotplug / resolution change mid-session still fits; tmpfs pages are
     * only charged for what we actually write, so being generous is cheap. */
    const size_t floor_bytes = (size_t)5120 * 2880 * 4;
    size_t slot_bytes = need * 2 > floor_bytes ? need * 2 : floor_bytes;
    uint32_t hdr_size = 4096;
    size_t total = hdr_size + slot_bytes * slots;
    if (ftruncate(fd, (off_t)total) < 0)
        die("ftruncate", errno);
    void *map = mmap(NULL, total, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (map == MAP_FAILED)
        die("mmap", errno);
    s.h = map;
    s.pixels = (uint8_t *)map + hdr_size;
    s.slot_bytes = slot_bytes;

    kwc_hdr_t *h = s.h;
    memset(h, 0, sizeof(*h));
    h->magic = KWC_MAGIC;
    h->version = KWC_VERSION;
    h->hdr_size = hdr_size;
    h->slot_bytes = (uint32_t)slot_bytes;
    h->slots = slots;
    h->daemon_pid = (uint32_t)getpid();
    h->width = f.width;
    h->height = f.height;
    h->stride = f.stride;
    h->format = f.format;
    h->scale = f.scale;
    snprintf(h->screen, sizeof(h->screen), "%s", f.screen);
    h->depth = (uint32_t)depth;
    h->fps = fps;

    /* frame 1 = the grab we just did */
    memcpy(s.pixels, tmp, need);
    free(tmp);
    h->target = (uint32_t)opts_target(o);
    if (o->window)
        snprintf(h->window, sizeof(h->window), "%s", o->window);

    kwc_slot_t *sl = &h->slot[0];
    sl->status = KWC_OK;
    sl->width = f.width;
    sl->height = f.height;
    sl->stride = f.stride;
    sl->format = f.format;
    sl->scale = f.scale;
    sl->grab_ms = gms;
    sl->total_ms = gms + rms;
    sl->ts_ns = f.ts_ns;
    snprintf(sl->screen, sizeof(sl->screen), "%s", f.screen);
    if (f.window[0])
        snprintf(h->window, sizeof(h->window), "%s", f.window);
    __atomic_store_n(&h->frame_seq, 1, __ATOMIC_RELEASE);
    __atomic_store_n(&h->published, 1, __ATOMIC_RELEASE);
    s.dispatched = 1;
    __atomic_store_n(&h->ready, 1, __ATOMIC_RELEASE);

    signal(SIGTERM, on_signal);
    signal(SIGINT, on_signal);
    signal(SIGPIPE, SIG_IGN);
    prctl(PR_SET_PDEATHSIG, SIGTERM); /* die with our client */
    s.last_activity_ns = now_ns();

    fprintf(stderr,
            "kwcapture: serving %ux%u stride=%u slots=%u depth=%d slot=%zuMiB shm=%s "
            "target=%s%s (first frame %.2f+%.2f ms)\n",
            f.width, f.height, f.stride, slots, depth, slot_bytes >> 20, shm_path,
            o->active_window ? "active-window" : o->window ? "window" : "screen",
            o->window ? o->window : "", gms, rms);

    struct pollfd pfds[NIFL + 1];
    while (!__atomic_load_n(&h->quit, __ATOMIC_ACQUIRE) && !g_sig) {
        /* what to capture next? */
        uint64_t want_target;
        if (s.frame_interval_ns) {
            uint64_t now = now_ns();
            if (now < s.next_due_ns) {
                want_target = s.dispatched; /* paced: not due yet */
            } else {
                s.next_due_ns = now + s.frame_interval_ns;
                want_target = s.dispatched + 1;
                s.last_activity_ns = now;
            }
        } else {
            want_target = __atomic_load_n(&h->req_seq, __ATOMIC_ACQUIRE);
        }
        while ((int64_t)(want_target - s.dispatched) > 0 && inflight_count(&s) < s.depth) {
            if (dispatch(&s) != 0)
                break;
        }

        int n = 0;
        pfds[n].fd = s.req_fd;
        pfds[n].events = POLLIN;
        pfds[n].revents = 0;
        n++;
        pfds[n].fd = sd_bus_get_fd(s.bus);
        pfds[n].events = (short)sd_bus_get_events(s.bus);
        pfds[n].revents = 0;
        n++;
        for (int i = 0; i < NIFL; i++) {
            if (!s.ifl[i].active || s.ifl[i].read_fd < 0)
                continue;
            pfds[n].fd = s.ifl[i].read_fd;
            pfds[n].events = POLLIN;
            pfds[n].revents = 0;
            n++;
        }
        int timeout = -1;
        if (s.frame_interval_ns) {
            uint64_t now = now_ns();
            timeout = now < s.next_due_ns ? (int)((s.next_due_ns - now) / 1000000ull) + 1 : 0;
        } else if (inflight_count(&s) == 0) {
            if (s.idle_exit_ns && now_ns() - s.last_activity_ns > s.idle_exit_ns) {
                fprintf(stderr, "kwcapture: idle, exiting\n");
                break;
            }
            timeout = 250;
        }
        if (poll(pfds, n, timeout) < 0 && errno != EINTR)
            die("poll", errno);

        if (pfds[0].revents & POLLIN) { /* flush the poke bytes */
            char junk[64];
            while (read(s.req_fd, junk, sizeof(junk)) > 0)
                ;
            s.last_activity_ns = now_ns();
        }

        while (sd_bus_process(s.bus, NULL) > 0)
            ;
        for (int i = 0; i < NIFL; i++)
            if (s.ifl[i].active)
                drain(&s, &s.ifl[i]);

        /* A request whose reply (or pixels) never arrive must not wedge the ring
         * either; KWin can be slow but 20 s is beyond anything real. */
        uint64_t now2 = now_ns();
        for (int i = 0; i < NIFL; i++) {
            inflight_t *in = &s.ifl[i];
            if (!in->active || now2 - in->sent_ns < 20000000000ull)
                continue;
            fprintf(stderr, "kwcapture: grab %llu timed out waiting for KWin\n",
                    (unsigned long long)in->seq);
            if (in->read_fd >= 0) {
                close(in->read_fd);
                in->read_fd = -1;
            }
            in->active = 0;
            in->done = 1;
            in->status = ETIMEDOUT;
            in->replied_ns = now2;
        }

        /* also publishes frames that failed (window closed, refused, empty): the D-Bus
         * callbacks have no server pointer with which to advance the ring */
        advance(&s);
    }
    __atomic_store_n(&h->magic, KWC_MAGIC_GONE, __ATOMIC_RELEASE);
    if (s.req_fd >= 0)
        close(s.req_fd);
    unlink(s.req_path);
    munmap(map, total);
    close(fd);
    sd_bus_unref(s.bus);
    return 0;
}

/* ==================================================================== list
 * Enumerate outputs straight from the Wayland registry (no special permission
 * needed).  wl_output.geometry width/height are in millimetres, so the pixel size
 * and refresh rate come from the current wl_output.mode event.
 */
#define MAXOUT 16
static struct {
    char name[64];
    int32_t x, y, px_w, px_h, refresh_hz1000, scale;
    int have_mode, have_geom;
} g_outs[MAXOUT];
static int g_nouts = 0;
static struct wl_display *g_dpy = NULL;

static void out_geometry(void *data, struct wl_output *o, int32_t x, int32_t y, int32_t pw_mm,
                         int32_t ph_mm, int32_t subpixel, const char *make,
                         const char *model, int32_t transform)
{
    (void)o;
    (void)pw_mm; /* physical size in millimetres, not pixels */
    (void)ph_mm;
    (void)subpixel;
    (void)make;
    (void)model;
    (void)transform;
    int idx = (int)(intptr_t)data;
    if (idx < 0 || idx >= MAXOUT)
        return;
    g_outs[idx].x = x;
    g_outs[idx].y = y;
    g_outs[idx].have_geom = 1;
}
static void out_name(void *data, struct wl_output *o, const char *name)
{
    (void)o;
    int idx = (int)(intptr_t)data;
    if (idx < 0 || idx >= MAXOUT)
        return;
    snprintf(g_outs[idx].name, sizeof(g_outs[idx].name), "%s", name ? name : "?");
}
static void out_description(void *data, struct wl_output *o, const char *description)
{
    (void)data;
    (void)o;
    (void)description;
}
static void out_mode(void *data, struct wl_output *o, uint32_t flags, int32_t w, int32_t h,
                     int32_t refresh)
{
    (void)o;
    int idx = (int)(intptr_t)data;
    if (idx < 0 || idx >= MAXOUT)
        return;
    if ((flags & WL_OUTPUT_MODE_CURRENT) && !g_outs[idx].have_mode) {
        g_outs[idx].px_w = w;
        g_outs[idx].px_h = h;
        g_outs[idx].refresh_hz1000 = refresh; /* mHz */
        g_outs[idx].have_mode = 1;
    }
}
static void out_done(void *data, struct wl_output *o)
{
    (void)data;
    (void)o;
}
static void out_scale(void *data, struct wl_output *o, int32_t f)
{
    (void)o;
    int idx = (int)(intptr_t)data;
    if (idx >= 0 && idx < MAXOUT)
        g_outs[idx].scale = f;
}
static const struct wl_output_listener g_out_listener = {
    .geometry = out_geometry,
    .mode = out_mode,
    .done = out_done,
    .scale = out_scale,
    .name = out_name,
    .description = out_description,
};

static void reg_global(void *data, struct wl_registry *reg, uint32_t id, const char *iface,
                       uint32_t ver)
{
    (void)data;
    if (strcmp(iface, "wl_output") || g_nouts >= MAXOUT)
        return;
    int idx = g_nouts++;
    void *o = wl_registry_bind(reg, id, &wl_output_interface, ver > 4 ? 4 : ver);
    wl_output_add_listener(o, &g_out_listener, (void *)(intptr_t)idx);
}
static void reg_global_remove(void *data, struct wl_registry *reg, uint32_t id)
{
    (void)data;
    (void)reg;
    (void)id;
}
static const struct wl_registry_listener g_reg_listener = {reg_global, reg_global_remove};

static int mode_list(void)
{
    g_dpy = wl_display_connect(NULL);
    if (!g_dpy)
        die("cannot connect to the Wayland compositor", EIO);
    struct wl_registry *reg = wl_display_get_registry(g_dpy);
    wl_registry_add_listener(reg, &g_reg_listener, NULL);
    wl_display_roundtrip(g_dpy);
    wl_display_roundtrip(g_dpy);
    for (int i = 0; i < g_nouts; i++) {
        if (!g_outs[i].have_geom)
            continue;
        printf("%s %dx%d %.2f %d %d %d\n", g_outs[i].name, g_outs[i].px_w, g_outs[i].px_h,
               g_outs[i].refresh_hz1000 / 1000.0, g_outs[i].x, g_outs[i].y,
               g_outs[i].scale > 0 ? g_outs[i].scale : 1);
    }
    wl_display_disconnect(g_dpy);
    return 0;
}

/* ========================================================== window listing
 * KWin's screenshot interface cannot enumerate windows, but two of its other
 * (unrestricted -- no desktop-file authorisation needed) interfaces give us exactly
 * what CaptureWindow() wants:
 *
 *   /WindowsRunner  org.kde.krunner1  Match(query s) -> a(sssida{sv})
 *       An empty query matches every *normal* window (Workspace::windows() minus
 *       desktops, docks, splash/override-redirect and unmanaged windows), and each
 *       match id is "<action>_<uuid>" where the uuid is Window::internalId().
 *   /KWin           org.kde.KWin      getWindowInfo(uuid s) -> a{sv}
 *       caption, resourceClass, geometry, minimized/fullscreen/..., one window.
 *
 * So: one Match() for the handles, one getWindowInfo() per window for the details.
 * If you do have a handle for a panel/wallpaper/overlay (a KWin script, the qml
 * console, ...), CaptureWindow() takes it just fine -- they are only missing from
 * this listing.
 */
#define MAXWIN 256

typedef struct {
    char uuid[64];
    char caption[256];
    char resource_class[128]; /* wayland app_id / X11 WM_CLASS */
    char resource_name[128];
    char desktop_file[128];
    char role[128];
    char icon[128];
    char desktops[8][64];
    int n_desktops;
    double x, y, width, height;
    int minimized, fullscreen, keep_above, keep_below, no_border, skip_taskbar,
        skip_pager, skip_switcher, max_h, max_v;
    long long type, layer;
} win_t;

/* One value of an a{sv} whose key we already read. */
static void wininfo_apply(sd_bus_message *m, const char *key, char type,
                          const char *contents, win_t *w)
{
    double num = 0;
    const char *str = NULL;
    int have_num = 0, have_str = 0;

    switch (type) {
    case 'b': {
        int v = 0;
        if (sd_bus_message_read_basic(m, 'b', &v) >= 0)
            num = v, have_num = 1;
        break;
    }
    case 'y':
    case 'n':
    case 'q':
    case 'i':
    case 'u': {
        uint32_t v = 0;
        if (sd_bus_message_read_basic(m, type, &v) >= 0) {
            num = (double)(int32_t)v; /* 'i' arrives zero-extended in a uint32 */
            have_num = 1;
        }
        break;
    }
    case 'x':
    case 't': {
        int64_t v = 0;
        if (sd_bus_message_read_basic(m, type, &v) >= 0)
            num = (double)v, have_num = 1;
        break;
    }
    case 'd': {
        double v = 0;
        if (sd_bus_message_read_basic(m, 'd', &v) >= 0)
            num = v, have_num = 1;
        break;
    }
    case 's': {
        const char *v = NULL;
        if (sd_bus_message_read_basic(m, 's', &v) >= 0 && v)
            str = v, have_str = 1;
        break;
    }
    case 'a': {
        /* only the desktop id list interests us; activities & co are skipped */
        if (contents && !strcmp(contents, "s") && !strcmp(key, "desktops")) {
            if (sd_bus_message_enter_container(m, 'a', "s") >= 0) {
                while (w->n_desktops < 8) {
                    const char *v = NULL;
                    if (sd_bus_message_read(m, "s", &v) <= 0)
                        break;
                    snprintf(w->desktops[w->n_desktops++], sizeof(w->desktops[0]), "%s",
                             v ? v : "");
                }
                sd_bus_message_exit_container(m);
            }
        } else {
            sd_bus_message_skip(m, NULL);
        }
        return; /* not a scalar: nothing to assign below */
    }
    default:
        break;
    }
    if (!have_num && !have_str) {
        sd_bus_message_skip(m, NULL);
        return;
    }
    /* KWin's key names are camelCase, our fields are not, so map them explicitly */
    if (have_str) {
#define STRFIELD(dbuskey, field)                                                         \
    if (!strcmp(key, dbuskey)) snprintf(w->field, sizeof(w->field), "%s", str)
        STRFIELD("caption", caption);
        STRFIELD("resourceClass", resource_class);
        STRFIELD("resourceName", resource_name);
        STRFIELD("desktopFile", desktop_file);
        STRFIELD("role", role);
        STRFIELD("icon", icon);
#undef STRFIELD
    }
    if (have_num) {
#define NUMFIELD(dbuskey, field)                                                         \
    if (!strcmp(key, dbuskey)) w->field = (int)num
        NUMFIELD("minimized", minimized);
        NUMFIELD("fullscreen", fullscreen);
        NUMFIELD("keepAbove", keep_above);
        NUMFIELD("keepBelow", keep_below);
        NUMFIELD("noBorder", no_border);
        NUMFIELD("skipTaskbar", skip_taskbar);
        NUMFIELD("skipPager", skip_pager);
        NUMFIELD("skipSwitcher", skip_switcher);
#undef NUMFIELD
        if (!strcmp(key, "x"))
            w->x = num;
        else if (!strcmp(key, "y"))
            w->y = num;
        else if (!strcmp(key, "width"))
            w->width = num;
        else if (!strcmp(key, "height"))
            w->height = num;
        else if (!strcmp(key, "maximizeHorizontal"))
            w->max_h = (int)num;
        else if (!strcmp(key, "maximizeVertical"))
            w->max_v = (int)num;
        else if (!strcmp(key, "type"))
            w->type = (long long)num;
        else if (!strcmp(key, "layer"))
            w->layer = (long long)num;
    }
}

static void parse_window_info(sd_bus_message *reply, win_t *w)
{
    if (sd_bus_message_enter_container(reply, 'a', "{sv}") < 0)
        return;
    while (sd_bus_message_enter_container(reply, 'e', "sv") > 0) {
        const char *key = NULL;
        sd_bus_message_read(reply, "s", &key);
        sd_bus_message_enter_container(reply, 'v', NULL);
        char type = 0;
        const char *contents = NULL;
        sd_bus_message_peek_type(reply, &type, &contents);
        if (key)
            wininfo_apply(reply, key, type, contents, w);
        else
            sd_bus_message_skip(reply, NULL);
        sd_bus_message_exit_container(reply);
        sd_bus_message_exit_container(reply);
    }
    sd_bus_message_exit_container(reply);
}

/* Every normal window: handles from /WindowsRunner, details from /KWin. */
static int collect_windows(sd_bus *bus, win_t *wins, int max)
{
    sd_bus_error error = SD_BUS_ERROR_NULL;
    sd_bus_message *reply = NULL;
    int n = 0;

    int r = sd_bus_call_method(bus, "org.kde.KWin", "/WindowsRunner", "org.kde.krunner1",
                               "Match", &error, &reply, "s", "");
    if (r < 0) {
        fprintf(stderr, "kwcapture: window list failed: %s\n",
                error.message ? error.message : "D-Bus call failed");
        sd_bus_error_free(&error);
        return -1;
    }
    if (sd_bus_message_enter_container(reply, 'a', "(sssida{sv})") >= 0) {
        while (n < max && sd_bus_message_enter_container(reply, 'r', NULL) > 0) {
            /* (id, text, icon, categoryRelevance, relevance, properties): sd-bus wants
             * every element consumed before we can leave the struct, and the properties
             * dict may carry an icon pixmap we do not want. */
            const char *id = NULL, *text = NULL, *icon = NULL;
            int32_t category = 0;
            double relevance = 0;
            int ok = sd_bus_message_read(reply, "sssid", &id, &text, &icon, &category,
                                         &relevance);
            sd_bus_message_skip(reply, "a{sv}");
            sd_bus_message_exit_container(reply);
            if (ok <= 0 || !id)
                continue;
            const char *underscore = strrchr(id, '_');
            const char *uuid = underscore ? underscore + 1 : id;
            int dup = 0;
            for (int i = 0; i < n; i++)
                if (!strcmp(wins[i].uuid, uuid))
                    dup = 1;
            if (!dup && *uuid) {
                snprintf(wins[n].uuid, sizeof(wins[n].uuid), "%s", uuid);
                n++;
            }
        }
        sd_bus_message_exit_container(reply);
    }
    sd_bus_message_unref(reply);

    for (int i = 0; i < n; i++) {
        sd_bus_error e2 = SD_BUS_ERROR_NULL;
        sd_bus_message *r2 = NULL;
        if (sd_bus_call_method(bus, "org.kde.KWin", "/KWin", "org.kde.KWin",
                               "getWindowInfo", &e2, &r2, "s", wins[i].uuid) >= 0) {
            parse_window_info(r2, &wins[i]);
            sd_bus_message_unref(r2);
        } else {
            sd_bus_error_free(&e2);
        }
        /* closed between the two calls: no info at all -> drop it */
        if (!wins[i].caption[0] && !wins[i].resource_class[0] && wins[i].width <= 0) {
            wins[i] = wins[n - 1];
            memset(&wins[n - 1], 0, sizeof(wins[n - 1]));
            n--;
            i--;
        }
    }
    return n;
}

static void json_string(FILE *f, const char *s)
{
    fputc('"', f);
    for (const unsigned char *p = (const unsigned char *)s; p && *p; p++) {
        if (*p == '"' || *p == '\\')
            fprintf(f, "\\%c", *p);
        else if (*p < 0x20)
            fprintf(f, "\\u%04x", *p);
        else
            fputc(*p, f);
    }
    fputc('"', f);
}

static void window_to_json(FILE *f, const win_t *w, int first)
{
    fprintf(f, "%s{", first ? "" : ",");
    fprintf(f, "\"id\":");
    json_string(f, w->uuid);
    fprintf(f, ",\"name\":");
    json_string(f, w->caption);
    fprintf(f, ",\"app_id\":");
    json_string(f, w->resource_class);
    fprintf(f, ",\"resource_name\":");
    json_string(f, w->resource_name);
    fprintf(f, ",\"desktop_file\":");
    json_string(f, w->desktop_file);
    fprintf(f, ",\"role\":");
    json_string(f, w->role);
    fprintf(f, ",\"icon\":");
    json_string(f, w->icon);
    fprintf(f, ",\"x\":%d,\"y\":%d,\"width\":%d,\"height\":%d", (int)w->x, (int)w->y,
            (int)w->width, (int)w->height);
    fprintf(f, ",\"minimized\":%s,\"fullscreen\":%s", w->minimized ? "true" : "false",
            w->fullscreen ? "true" : "false");
    fprintf(f, ",\"keep_above\":%s,\"keep_below\":%s,\"no_border\":%s",
            w->keep_above ? "true" : "false", w->keep_below ? "true" : "false",
            w->no_border ? "true" : "false");
    fprintf(f, ",\"skip_taskbar\":%s,\"skip_pager\":%s,\"skip_switcher\":%s",
            w->skip_taskbar ? "true" : "false", w->skip_pager ? "true" : "false",
            w->skip_switcher ? "true" : "false");
    fprintf(f, ",\"maximized\":%s", (w->max_h && w->max_v) ? "true" : "false");
    fprintf(f, ",\"window_type\":%lld,\"layer\":%lld", w->type, w->layer);
    fprintf(f, ",\"desktops\":[");
    for (int i = 0; i < w->n_desktops; i++)
        fprintf(f, "\"%s\"%s", w->desktops[i], i + 1 < w->n_desktops ? "," : "");
    fprintf(f, "]}");
}

/* Cut a UTF-8 string at `chars` codepoints (table output only). */
static void utf8_clip(char *dst, size_t dstsz, const char *src, size_t chars)
{
    size_t seen = 0, i = 0;
    while (src[i] && seen < chars) {
        size_t step = 1;
        unsigned char c = (unsigned char)src[i];
        if (c >= 0xf0)
            step = 4;
        else if (c >= 0xe0)
            step = 3;
        else if (c >= 0xc0)
            step = 2;
        if (step > 1 && src[i + step] == '\0')
            break; /* truncated sequence at the end */
        if (i + step >= dstsz)
            break;
        seen++;
        i += step;
    }
    size_t n = i > dstsz - 1 ? dstsz - 1 : i;
    memcpy(dst, src, n);
    dst[n] = '\0';
}

static void window_to_table(FILE *f, const win_t *w)
{
    char name[192] = {0}, app[96] = {0};
    utf8_clip(name, sizeof(name), w->caption, 46);
    utf8_clip(app, sizeof(app), w->resource_class[0] ? w->resource_class : w->desktop_file, 26);
    for (char *p = name; *p; p++)
        if ((unsigned char)*p < 0x20)
            *p = ' ';
    for (char *p = app; *p; p++)
        if ((unsigned char)*p < 0x20)
            *p = ' ';
    char flags[64] = {0};
    if (w->minimized)
        strcat(flags, "minimized,");
    if (w->fullscreen)
        strcat(flags, "fullscreen,");
    if (w->max_h && w->max_v)
        strcat(flags, "maximized,");
    if (w->keep_above)
        strcat(flags, "above,");
    if (w->keep_below)
        strcat(flags, "below,");
    if (w->skip_taskbar)
        strcat(flags, "skip-taskbar,");
    if (flags[0])
        flags[strlen(flags) - 1] = '\0';
    fprintf(f, "%-38s  %-46s  %-26s  %4dx%-4d %+5d,%-6d %s\n", w->uuid, name, app,
            (int)w->width, (int)w->height, (int)w->x, (int)w->y, flags);
}

static int mode_list_windows(sd_bus *bus, int as_json)
{
    static win_t wins[MAXWIN];
    int n = collect_windows(bus, wins, MAXWIN);
    if (n < 0)
        return 1;
    if (as_json) {
        printf("[");
        for (int i = 0; i < n; i++)
            window_to_json(stdout, &wins[i], i == 0);
        printf("]\n");
        return 0;
    }
    printf("%-38s  %-46s  %-26s  %-9s  %s\n", "WINDOW HANDLE (id)", "NAME", "APP_ID",
           "SIZE", "POSITION / FLAGS");
    for (int i = 0; i < n; i++)
        window_to_table(stdout, &wins[i]);
    if (!n)
        printf("(no normal windows: KWin lists application windows only, not panels, "
               "overlays or the desktop)\n");
    return 0;
}

/* --window accepts a handle from --list-windows, or an exact (case-insensitive) name:
 * caption, app id, desktop file or resource name, matching exactly one window.  The
 * Python API additionally allows unique substring matches. */
static int looks_like_handle(const char *s)
{
    size_t n = strlen(s);
    if (n >= 2 && s[0] == '{' && s[n - 1] == '}')
        return 1;
    return n == 36 && s[8] == '-' && s[13] == '-' && s[18] == '-' && s[23] == '-';
}

/* QUuid accepts "2c14...-..." and "{2c14...-...}"; treat them as the same handle. */
static int handle_eq(const char *a, const char *b)
{
    while (*a == '{')
        a++;
    while (*b == '{')
        b++;
    size_t la = strcspn(a, "}"), lb = strcspn(b, "}");
    return la == lb && !strncasecmp(a, b, la);
}

static int name_matches(const win_t *w, const char *spec)
{
    return !strcasecmp(w->caption, spec) ||
           (w->resource_class[0] && !strcasecmp(w->resource_class, spec)) ||
           (w->desktop_file[0] && !strcasecmp(w->desktop_file, spec)) ||
           (w->resource_name[0] && !strcasecmp(w->resource_name, spec));
}

static void list_windows_stderr(const win_t *wins, int n)
{
    for (int i = 0; i < n; i++)
        fprintf(stderr, "  %-38s %s\n", wins[i].uuid, wins[i].caption);
}

/* Returns the handle to use (a pointer that stays valid), or NULL after printing why. */
static const char *resolve_window_handle(sd_bus *bus, const char *spec)
{
    static win_t wins[MAXWIN];
    int n = collect_windows(bus, wins, MAXWIN);
    if (n < 0)
        return NULL;
    if (looks_like_handle(spec)) {
        for (int i = 0; i < n; i++)
            if (handle_eq(wins[i].uuid, spec))
                return wins[i].uuid; /* KWin's own spelling of the handle */
        fprintf(stderr, "kwcapture: no window with handle '%s' -- available:\n", spec);
        list_windows_stderr(wins, n);
        return NULL;
    }
    int hit = -1, hits = 0;
    for (int i = 0; i < n; i++)
        if (name_matches(&wins[i], spec)) {
            hit = i;
            hits++;
        }
    if (hits == 1)
        return wins[hit].uuid;
    if (hits > 1) {
        fprintf(stderr, "kwcapture: '%s' matches %d windows -- pick one by handle:\n", spec,
                hits);
        for (int i = 0; i < n; i++)
            if (name_matches(&wins[i], spec))
                fprintf(stderr, "  %-38s %s\n", wins[i].uuid, wins[i].caption);
        return NULL;
    }
    fprintf(stderr, "kwcapture: no window matches '%s' -- available:\n", spec);
    list_windows_stderr(wins, n);
    return NULL;
}

/* ==================================================================== main */
static void usage(const char *argv0)
{
    fprintf(stderr,
            "kwcapture - fast screen capture on KDE Plasma (Wayland)\n"
            "usage: %s [mode] [options]\n"
            "\n"
            "modes:\n"
            "  (default)          grab one frame\n"
            "  --list             list outputs: NAME WxH refresh x y scale\n"
            "  --list-windows     list capturable windows (handle, name, app, geometry)\n"
            "  --bench N          grab N frames and report timings\n"
            "  serve              resident daemon: frames in shared memory for clients\n"
            "\n"
            "options:\n"
            "  --screen NAME      output to capture (e.g. DP-1); default: active screen\n"
            "  --area X,Y,W,H     capture a region (logical coordinates)\n"
            "  --workspace        capture the whole virtual desktop\n"
            "  --window HANDLE    capture one window: a handle from --list-windows, or an\n"
            "                     exact (case-insensitive) window name / app id\n"
            "  --active-window    capture the window that has focus\n"
            "  --json             with --list-windows: machine-readable output\n"
            "  --out FILE         raw BGRA8888 output ('-' = stdout, default)\n"
            "  --cursor           include the hardware cursor\n"
            "  --decoration       include window decorations and shadows\n"
            "  --no-hide-caller   do not hide this process' own windows\n"
            "  --shm PATH         shared memory file for serve mode\n"
            "  --slots N          ring slots, default 4\n"
            "  --depth N          requests in flight to KWin, default 2\n"
            "  --fps N            serve: capture continuously at N frames/s\n"
            "  --idle-exit SEC    serve: quit after SEC idle seconds (0 = never)\n"
            "  --quiet            less chatter\n",
            argv0);
    exit(2);
}

int main(int argc, char **argv)
{
    opts_t o = {0};
    o.include_shadow = 1;
    o.native_resolution = 1;
    o.hide_caller_windows = 1;
    const char *out_path = "-";
    const char *shm_path = NULL;
    const char *window_spec = NULL;
    int bench = 0, quiet = 0, serve = 0, depth = 2;
    int list_windows = 0, as_json = 0;
    uint32_t slots = 4;
    double fps = 0, idle_exit = 120;

    for (int i = 1; i < argc; i++) {
        const char *a = argv[i];
        if (!strcmp(a, "--list"))
            return mode_list();
        else if (!strcmp(a, "--list-windows") || !strcmp(a, "windows"))
            list_windows = 1;
        else if (!strcmp(a, "--json"))
            as_json = 1;
        else if (!strcmp(a, "serve"))
            serve = 1;
        else if (!strcmp(a, "--window") && i + 1 < argc)
            window_spec = argv[++i];
        else if (!strcmp(a, "--active-window"))
            o.active_window = 1;
        else if (!strcmp(a, "--screen") && i + 1 < argc)
            o.screen = argv[++i];
        else if (!strcmp(a, "--area") && i + 1 < argc) {
            if (sscanf(argv[++i], "%d,%d,%d,%d", &o.area[0], &o.area[1], &o.area[2],
                       &o.area[3]) != 4)
                usage(argv[0]);
            o.use_area = 1;
        } else if (!strcmp(a, "--workspace"))
            o.use_workspace = 1;
        else if (!strcmp(a, "--out") && i + 1 < argc)
            out_path = argv[++i];
        else if (!strcmp(a, "--shm") && i + 1 < argc)
            shm_path = argv[++i];
        else if (!strcmp(a, "--slots") && i + 1 < argc)
            slots = (uint32_t)atoi(argv[++i]);
        else if (!strcmp(a, "--depth") && i + 1 < argc)
            depth = atoi(argv[++i]);
        else if (!strcmp(a, "--fps") && i + 1 < argc)
            fps = atof(argv[++i]);
        else if (!strcmp(a, "--idle-exit") && i + 1 < argc)
            idle_exit = atof(argv[++i]);
        else if (!strcmp(a, "--bench") && i + 1 < argc)
            bench = atoi(argv[++i]);
        else if (!strcmp(a, "--cursor"))
            o.include_cursor = 1;
        else if (!strcmp(a, "--decoration"))
            o.include_decoration = o.include_shadow = 1;
        else if (!strcmp(a, "--no-hide-caller"))
            o.hide_caller_windows = 0;
        else if (!strcmp(a, "--quiet"))
            quiet = 1;
        else if (!strcmp(a, "--help") || !strcmp(a, "-h"))
            usage(argv[0]);
        else
            usage(argv[0]);
    }
    if (slots < 1 || slots > KWC_MAX_SLOTS)
        die("--slots out of range", EINVAL);
    if (depth < 1 || depth > NIFL)
        die("--depth out of range", EINVAL);
    if (window_spec && o.active_window)
        die("--window and --active-window are mutually exclusive", EINVAL);
    if ((window_spec || o.active_window) && (o.use_area || o.use_workspace || o.screen))
        die("a window capture cannot also be a screen/area/workspace capture", EINVAL);

    sd_bus *bus = NULL;
    if (list_windows || window_spec) {
        if (sd_bus_open_user(&bus) < 0)
            die("cannot reach the session bus", EIO);
    }
    if (list_windows) {
        int rc = mode_list_windows(bus, as_json);
        if (bus)
            sd_bus_unref(bus);
        return rc;
    }
    if (window_spec) {
        o.window = resolve_window_handle(bus, window_spec);
        if (!o.window) {
            sd_bus_unref(bus);
            return 1;
        }
    }

    if (serve) {
        char def[256];
        if (!shm_path) {
            const char *rt = getenv("XDG_RUNTIME_DIR");
            snprintf(def, sizeof(def), "%s/kwcapture.shm", rt ? rt : "/tmp");
            shm_path = def;
        }
        if (bus)
            sd_bus_unref(bus); /* serve() opens its own connection */
        return mode_serve(&o, shm_path, slots, depth, fps, idle_exit);
    }

    if (!bus && sd_bus_open_user(&bus) < 0)
        die("cannot reach the session bus", EIO);
    uint8_t *buf = NULL;
    size_t cap = 0;
    frame_out_t f = {0};
    double gms = 0, rms = 0;

    if (bench) {
        double sum_g = 0, sum_r = 0;
        uint64_t t_start = now_ns(), t_last = now_ns();
        for (int it = 0; it < bench; it++) {
            int r = grab_sync(bus, &o, &buf, &cap, &f, &gms, &rms);
            if (r < 0)
                die("grab failed", r);
            sum_g += gms;
            sum_r += rms;
            uint64_t now = now_ns();
            if (!quiet && (it < 3 || it == bench - 1))
                fprintf(stderr, "  frame %3d  grab %6.2f ms  read %5.2f ms  wall %6.2f ms\n", it,
                        gms, rms, ms_between(t_last, now));
            t_last = now;
        }
        double total_ms = ms_between(t_start, now_ns()) / bench;
        fprintf(stderr,
                "kwcapture: %d frames %ux%u  grab %.2fms + read %.2fms  =>  %.2f ms/frame, "
                "%.1f fps\n",
                bench, f.width, f.height, sum_g / bench, sum_r / bench, total_ms, 1000.0 / total_ms);
    } else {
        int r = grab_sync(bus, &o, &buf, &cap, &f, &gms, &rms);
        if (r < 0)
            die("grab failed", r);
        FILE *out = (!strcmp(out_path, "-") || !strcmp(out_path, "")) ? stdout
                                                                     : fopen(out_path, "wb");
        if (!out)
            die(out_path, errno);
        fwrite(buf, 1, (size_t)f.stride * f.height, out);
        if (out != stdout)
            fclose(out);
        if (!quiet)
            fprintf(stderr,
                    "kwcapture: %ux%u stride=%u format=%u scale=%.1f %s%s grab=%.2fms "
                    "read=%.2fms\n",
                    f.width, f.height, f.stride, f.format, f.scale,
                    f.window[0] ? "window=" : (f.screen[0] ? "screen=" : ""),
                    f.window[0] ? f.window : f.screen, gms, rms);
    }
    free(buf);
    sd_bus_unref(bus);
    return 0;
}
