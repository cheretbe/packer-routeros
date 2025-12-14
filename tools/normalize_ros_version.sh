#!/bin/bash

# Normalize RouterOS version to ensure proper semantic versioning
# Usage: normalize_ros_version.sh <version>
#
# RouterOS versions can be in formats like:
# - "7.12" -> "7.12.0"
# - "6.49.1" -> "6.49.1"
# - "7.12.1" -> "7.12.1"
#
# This ensures consistent version comparison by adding ".0" patch version if missing.

if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>" >&2
    exit 1
fi

version="$1"

# Normalize version based on existing number of version separators
case $(echo "$version" | grep -o '\.' | wc -l) in
  0) normalized_version="$version.0.0" ;;
  1) normalized_version="$version.0" ;;
  *) normalized_version="$version" ;;
esac

echo "{\"raw\": \"$version\", \"normalized\": \"$normalized_version\"}"