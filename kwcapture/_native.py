"""Find (or build) the native capture helper that talks to KWin.

KWin authorises `org.kde.KWin.ScreenShot2` callers by looking at
`/proc/<pid>/exe`, so the capture must be a *native* process - a Python interpreter
can never be authorised.  That helper is:

  1. `$KWCAPTURE_BIN`, if you set it,
  2. `kwcapture/bin/kwcapture` — shipped inside the wheel when it could be built
     during `pip install`,
  3. `~/.cache/kwcapture/kwcapture-<version>-<arch>` — built on first use,
  4. built here and now from `kwcapture/native/kwcapture.c`.

Building needs a C compiler plus the libsystemd (sd-bus) and wayland-client develop-
ment headers; `NativeBuildError` spells out the package names when that fails.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
NATIVE_DIR = PKG_DIR / "native"
SOURCE = NATIVE_DIR / "kwcapture.c"
INCLUDE_DIR = NATIVE_DIR / "include"
ENV_VAR = "KWCAPTURE_BIN"
PKGS = ("libsystemd", "wayland-client")

BUILD_HINT = """build dependencies are missing.  The helper needs a C compiler and the
sd-bus / wayland client headers:

    Debian/Ubuntu:  sudo apt install build-essential libsystemd-dev libwayland-dev
    Fedora:         sudo dnf install gcc systemd-devel wayland-devel
    Arch:           sudo pacman -S base-devel systemd wayland

Or build it yourself and point kwcapture at it:
    cc -O2 -I{kinc} -o kwcapture {src} -lsystemd -lwayland-client
    export KWCAPTURE_BIN=$PWD/kwcapture""".format(
    kinc=INCLUDE_DIR, src=SOURCE
)


class NativeBuildError(RuntimeError):
    """The native helper could not be found or compiled."""


def prebuilt_path() -> Path:
    """Where `pip install` drops the compiled helper inside the package."""
    return PKG_DIR / "bin" / "kwcapture"


def cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "kwcapture"


def cache_path() -> Path:
    from . import __version__

    return cache_dir() / f"kwcapture-{__version__}-{platform.machine()}"


def candidate_binaries() -> list[Path]:
    out: list[Path] = []
    env = os.environ.get(ENV_VAR)
    if env:
        out.append(Path(env).expanduser())
    out += [prebuilt_path(), cache_path()]
    return out


# ELF e_machine values, so a wheel built on another CPU never gets exec'd.
_ELF_MACHINES = {
    "x86_64": 62,
    "aarch64": 183,
    "armv7l": 40,
    "i686": 3,
    "riscv64": 243,
    "ppc64le": 21,
}


def binary_matches_arch(path: Path) -> bool:
    """True if `path` can run here (ELF machine check; non-ELF files pass)."""
    want = _ELF_MACHINES.get(platform.machine())
    if want is None:
        return True
    try:
        with open(path, "rb") as f:
            head = f.read(20)
    except OSError:
        return False
    if head[:4] != b"\x7fELF":
        return True
    return len(head) >= 20 and int.from_bytes(head[18:20], "little") == want


def find_binary() -> Path | None:
    for path in candidate_binaries():
        if path.is_file() and os.access(path, os.X_OK) and binary_matches_arch(path):
            return path
    return None


def compiler_command(dest: Path, native_arch: bool = False) -> list[str]:
    cc = os.environ.get("CC") or shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if not cc:
        raise NativeBuildError("no C compiler found (set $CC or install build-essential)")
    cmd = [cc, "-O2", "-std=gnu11", "-D_GNU_SOURCE",
           f"-I{INCLUDE_DIR}", "-o", str(dest), str(SOURCE)]
    if native_arch or os.environ.get("KWCAPTURE_NATIVE"):
        cmd.insert(1, "-march=native")  # faster, but not portable to other CPUs
    pkgconfig = shutil.which("pkg-config")
    cflags: list[str] = []
    libs: list[str] = []
    if pkgconfig:
        try:
            cflags = subprocess.run([pkgconfig, "--cflags", *PKGS], capture_output=True,
                                    text=True, check=True).stdout.split()
        except subprocess.CalledProcessError:
            cflags = []
        try:
            libs = subprocess.run([pkgconfig, "--libs", *PKGS], capture_output=True,
                                  text=True, check=True).stdout.split()
        except subprocess.CalledProcessError:
            libs = ["-lsystemd", "-lwayland-client"]
    else:  # no pkg-config: the usual library names work on any freedesktop distro
        libs = ["-lsystemd", "-lwayland-client", "-lm"]
    return cmd + cflags + libs


def build_binary(dest: Path | None = None, native_arch: bool = False,
                 verbose: bool = False) -> Path:
    """Compile the helper.  Returns the path to the executable."""
    if not SOURCE.is_file():
        raise NativeBuildError(
            f"native source is missing ({SOURCE}); reinstall the kwcapture package"
        )
    dest = Path(dest) if dest else cache_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.parent / f".{dest.name}.building"
    cmd = compiler_command(tmp, native_arch=native_arch)
    if verbose:
        print("building:", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as e:
        raise NativeBuildError(f"could not run {cmd[0]}: {e}\n\n{BUILD_HINT}") from e
    if proc.returncode != 0:
        try:
            tmp.unlink()
        except OSError:
            pass
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-12:]
        raise NativeBuildError(
            "failed to compile the kwcapture helper:\n  "
            + "\n  ".join(tail)
            + f"\n\n{BUILD_HINT}"
        )
    os.replace(tmp, dest)
    os.chmod(dest, 0o755)
    return dest


def resolve(explicit: "Path | str | None" = None, allow_build: bool = True) -> Path:
    """An explicit path if given (and it exists), else find/build the helper."""
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise NativeBuildError(f"no such kwcapture helper: {path}")
        return path
    return ensure_binary(allow_build=allow_build)


def ensure_binary(allow_build: bool = True, verbose: bool = False) -> Path:
    """Path to a usable helper, compiling it into the user cache if necessary."""
    path = find_binary()
    if path:
        return path
    if not allow_build:
        raise NativeBuildError(
            "kwcapture helper not found (looked at: "
            + ", ".join(str(p) for p in candidate_binaries())
            + f")\n\n{BUILD_HINT}"
        )
    return build_binary(verbose=verbose)
