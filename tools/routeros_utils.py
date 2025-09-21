"""
RouterOS utilities for packer-routeros project.
"""

import packaging.version


def normalize_routeros_version(version_str):
    """
    Normalize RouterOS version to ensure proper semantic versioning and return a Version object.

    RouterOS versions can be in formats like:
    - "7.12" -> "7.12.0"
    - "6.49.1" -> "6.49.1"
    - "7.12.1" -> "7.12.1"

    This ensures consistent version comparison.
    """
    parts = version_str.split(".")
    # Ensure we have at least major.minor.patch format
    while len(parts) < 3:
        parts.append("0")

    return packaging.version.Version(".".join(parts))
