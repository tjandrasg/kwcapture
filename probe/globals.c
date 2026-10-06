/* Dump every global advertised by the Wayland compositor. */
#include <stdio.h>
#include <string.h>
#include <wayland-client.h>

static void global_add(void *data, struct wl_registry *reg, uint32_t id,
                       const char *iface, uint32_t ver) {
    (void)data;
    printf("%-46s v%-3u name=%u\n", iface, ver, id);
}
static void global_rem(void *data, struct wl_registry *reg, uint32_t id) {
    (void)data; (void)reg;
    printf("(gone) name=%u\n", id);
}
static const struct wl_registry_listener listener = {global_add, global_rem};

int main(void) {
    struct wl_display *dpy = wl_display_connect(NULL);
    if (!dpy) { fprintf(stderr, "cannot connect to wayland\n"); return 1; }
    struct wl_registry *reg = wl_display_get_registry(dpy);
    wl_registry_add_listener(reg, &listener, NULL);
    wl_display_roundtrip(dpy);
    wl_display_roundtrip(dpy);
    wl_display_disconnect(dpy);
    return 0;
}
