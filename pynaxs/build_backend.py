"""Custom PEP 517 build backend for pynaxs.

Delegates everything to ``setuptools.build_meta`` but first *vendors*
the NAXS JSON Schema — whose source of truth lives in the sibling
``../naxs/vX.Y/`` specification directories — into the ``pynaxs``
package so it is packaged into sdists and wheels.

Version constraint
------------------
The package's ``major.minor`` version must equal the latest schema
version (the highest ``vX.Y`` directory under ``../naxs/``, or the
``spec_version`` enum declared inside the schema file): while the
latest schema is ``v0.1``, pynaxs must be ``0.1.x``. A build with a
mismatched version fails with a descriptive error, so an inconsistent
release cannot even be built locally.

The generated ``pynaxs/schema.json`` is a build artifact: it is
excluded from version control via ``.gitignore`` and is regenerated
from the specification on every build. When building from an sdist
(where the sibling specification tree does not exist), the
pre-vendored copy shipped inside the sdist is used, and the version
constraint is re-verified against it.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from setuptools import build_meta as _orig
from setuptools.build_meta import *  # noqa: F401,F403  (re-export the full backend API)

_PROJECT_ROOT = Path(__file__).resolve().parent
_SPEC_ROOT = _PROJECT_ROOT.parent / "naxs"
_PYPROJECT = _PROJECT_ROOT / "pyproject.toml"
_SCHEMA_DST = _PROJECT_ROOT / "pynaxs" / "schema.json"

_SPEC_DIR_RE = re.compile(r"^v(\d+)\.(\d+)$")


def _package_version() -> str:
    """Return the project version declared in pyproject.toml.

    Uses a regex rather than tomllib so the check also works when the
    build runs on Python 3.9/3.10 (which lack tomllib).
    """
    text = _PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if m is None:
        raise RuntimeError(f"No 'version' field found in {_PYPROJECT}")
    return m.group(1)


def _latest_spec_schema() -> Path | None:
    """Return the newest ``naxs/vX.Y/schema.json``, or ``None``.

    ``None`` means the sibling specification tree is absent (e.g. the
    project is being built from an unpacked sdist), in which case the
    pre-vendored ``pynaxs/schema.json`` must be used instead.
    """
    if not _SPEC_ROOT.is_dir():
        return None
    dirs = [
        p for p in _SPEC_ROOT.iterdir()
        if p.is_dir() and _SPEC_DIR_RE.match(p.name)
    ]
    if not dirs:
        return None
    latest = max(
        dirs,
        key=lambda p: tuple(int(g) for g in _SPEC_DIR_RE.match(p.name).groups()),
    )
    schema = latest / "schema.json"
    return schema if schema.is_file() else None


def _schema_version(schema_path: Path) -> str:
    """Return the schema's declared spec version, e.g. ``"0.1"``.

    Reads ``properties.spec_version.enum[0]`` from the schema file;
    falls back to the ``vX.Y`` directory name (useful when the enum
    is missing or the schema lives outside a versioned directory).
    """
    try:
        with open(schema_path) as f:
            schema = json.load(f)
        enum = (
            schema.get("properties", {})
            .get("spec_version", {})
            .get("enum", [])
        )
        if len(enum) == 1:
            return str(enum[0])
    except (OSError, ValueError):
        pass
    m = _SPEC_DIR_RE.match(schema_path.parent.name)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    raise RuntimeError(
        f"Cannot determine schema version from {schema_path}: no usable "
        "properties.spec_version.enum and no vX.Y parent directory"
    )


def _enforce_version_constraint(pkg_version: str, schema_version: str) -> None:
    """Require the package's major.minor to equal the schema version.

    Example: while the schema is ``v0.1``, only ``0.1.x`` package
    versions are allowed (``0.1.0``, ``0.1.3``, ...).
    """
    parts = pkg_version.split(".")
    pkg_mm = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else pkg_version
    if pkg_mm != schema_version:
        raise RuntimeError(
            f"Version constraint violated: pynaxs is {pkg_version} but the "
            f"vendored schema is v{schema_version}. While the latest schema "
            f"is v{schema_version}, pynaxs must stay {schema_version}.x. "
            "Bump the package version together with the schema (or point "
            "the build at the matching naxs/vX.Y specification)."
        )


def _vendor_schema() -> None:
    """Copy the latest specification schema into the package.

    Raises:
        FileNotFoundError: Building outside the specification tree
            without a pre-vendored ``pynaxs/schema.json``.
        RuntimeError: The version constraint is violated, or the
            schema or package version cannot be determined.
    """
    pkg_version = _package_version()
    src = _latest_spec_schema()

    if src is not None:
        _enforce_version_constraint(pkg_version, _schema_version(src))
        _SCHEMA_DST.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, _SCHEMA_DST)
    elif _SCHEMA_DST.is_file():
        # Building from an sdist: the pre-vendored copy is the schema
        # source of truth; re-verify the constraint against it.
        _enforce_version_constraint(pkg_version, _schema_version(_SCHEMA_DST))
    else:
        raise FileNotFoundError(
            f"Cannot build pynaxs: no schema found under {_SPEC_ROOT} and "
            f"no pre-vendored copy at {_SCHEMA_DST}. Building from an "
            "sdist requires the vendored pynaxs/schema.json to be present."
        )


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    _vendor_schema()
    return _orig.build_wheel(wheel_directory, config_settings, metadata_directory)


def build_sdist(sdist_directory, config_settings=None):
    _vendor_schema()
    return _orig.build_sdist(sdist_directory, config_settings)


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    _vendor_schema()
    return _orig.build_editable(wheel_directory, config_settings, metadata_directory)
