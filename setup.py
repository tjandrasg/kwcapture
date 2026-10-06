"""Build glue: compile the native capture helper into the wheel.

KWin authorises `org.kde.KWin.ScreenShot2` by `/proc/<pid>/exe`, so the capture has to be
a native binary rather than a Python process.  `setup.py` builds it with the system C
compiler during `pip install`; if that fails (no compiler, no libsystemd/wayland headers)
we still produce a working Python package, because `kwcapture` recompiles the bundled
source on first use and prints actionable instructions if that is impossible too.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

try:  # setuptools vendors bdist_wheel; fall back to the wheel package
    from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
except ImportError:  # pragma: no cover
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

HERE = Path(__file__).resolve().parent
SRC = HERE / "kwcapture" / "native" / "kwcapture.c"
INC = HERE / "kwcapture" / "native" / "include"
PKGS = ("libsystemd", "wayland-client")

HELP = """\
*** kwcapture: could not build the native helper.
*** The wheel will still install; kwcapture will try to compile it on first use and
*** will print the packages you need if that fails too.
"""


def _pkgconfig(flag: str) -> list[str]:
    pc = shutil.which("pkg-config")
    if not pc:
        return []
    try:
        return subprocess.run([pc, flag, *PKGS], capture_output=True, text=True,
                              check=True).stdout.split()
    except (subprocess.CalledProcessError, OSError):
        return []


def compile_helper(dest_dir: Path, verbose: bool = True) -> Path | None:
    """Compile kwcapture.c into dest_dir/kwcapture.  Returns None on failure."""
    cc = os.environ.get("CC") or shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if not cc or not SRC.is_file():
        sys.stderr.write(HELP)
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / "kwcapture"
    libs = _pkgconfig("--libs") or ["-lsystemd", "-lwayland-client", "-lm"]
    cmd = [cc, "-O2", "-std=gnu11", "-D_GNU_SOURCE", f"-I{INC}", "-o", str(out), str(SRC)]
    if os.environ.get("KWCAPTURE_NATIVE"):
        cmd.insert(1, "-march=native")
    cmd += _pkgconfig("--cflags") + libs
    if verbose:
        print("kwcapture: building helper:", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write("".join(f"*** {line}\n" for line in proc.stderr.splitlines()[-15:]))
        sys.stderr.write(HELP)
        return None
    os.chmod(out, 0o755)
    return out


class build_py_with_native(build_py):
    """Mark the wheel platform-specific and drop the compiled helper inside it."""

    def finalize_options(self) -> None:  # type: ignore[override]
        super().finalize_options()
        self.root_is_pure = False

    def run(self) -> None:  # type: ignore[override]
        super().run()
        dest = Path(self.build_lib) / "kwcapture" / "bin"
        built = compile_helper(dest, verbose=self.verbose)
        if built is None:
            # ship the source only; kwcapture._native.build_binary() handles the rest
            dest.mkdir(parents=True, exist_ok=True)


class bdist_wheel(_bdist_wheel):
    """The wheel carries a compiled helper, so tag it for this platform."""

    def get_tag(self):  # type: ignore[override]
        python, abi, plat = super().get_tag()
        if plat in (None, "any"):
            plat = f"linux_{platform.machine()}"
        return python, abi, plat


setup(cmdclass={"build_py": build_py_with_native, "bdist_wheel": bdist_wheel})
