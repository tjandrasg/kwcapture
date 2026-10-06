CC      ?= gcc
PKG_CFLAGS := $(shell pkg-config --cflags libsystemd 2>/dev/null)
PKG_LIBS   := $(shell pkg-config --libs libsystemd wayland-client 2>/dev/null || echo -lsystemd -lwayland-client -lm)
CFLAGS  ?= -O2 -Wall -Wextra

PY   ?= $(CURDIR)/.venv/bin/python
BIN  := kwcapture/bin/kwcapture
SRC  := kwcapture/native/kwcapture.c
DEPS := kwcapture/native/include/kwcapture_shm.h

all: $(BIN)                 ## build the native helper into the package

# -march=native is for the dev build on this machine; the wheel uses portable -O2.
$(BIN): $(SRC) $(DEPS)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -march=native $(PKG_CFLAGS) -Ikwcapture/native/include -o $@ $(SRC) $(PKG_LIBS)

install-desktop: $(BIN)     ## tell KWin this binary may take screenshots
	$(PY) -m kwcapture install-desktop

setup: all install-desktop  ## one-time: build + authorise
	$(PY) -m kwcapture doctor

doctor:                     ## what's wrong?
	$(PY) -m kwcapture doctor --fix --build

test: $(BIN)
	$(PY) tests/test_kwcapture.py

bench: $(BIN)               ## kwcapture vs mss vs PIL
	$(PY) bench.py 3

demo: $(BIN)
	$(PY) -m kwcapture demo --frames 60 --width 1280 --save /tmp/kwcapture_demo.png

wheel: check-venv           ## build a wheel into dist/
	$(PY) -m pip wheel --no-deps -w dist .

sdist: check-venv
	$(PY) -m pip install build >/dev/null && $(PY) -m build --sdist

dev-install: check-venv     ## pip install this checkout into the venv
	$(PY) -m pip install -e .

check-venv:
	@test -x "$(PY)" || { echo "no $(PY); create it: python3 -m venv .venv && .venv/bin/pip install numpy pillow opencv-python-headless"; exit 1; }

clean:
	rm -rf build dist *.egg-info kwcapture/bin __pycache__ kwcapture/__pycache__ tests/__pycache__

.PHONY: all install-desktop setup doctor test bench demo wheel sdist dev-install clean
