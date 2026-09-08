"""
Validators for digital twin fields that need loose but safe constraints.

"""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import constr

# Loose UUID: alphanumeric, underscore, hyphen; length 1-64
UUID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
LooseUUID = Annotated[str, constr(pattern=UUID_PATTERN)]

# ISO8601-like timestamp: broad but not empty, max 64 chars
TIMESTAMP_PATTERN = re.compile(r"^[^\s]{1,64}$")  # no whitespace, length 1-64
LooseTimestamp = Annotated[str, constr(pattern=TIMESTAMP_PATTERN)]

# Loose string for descriptions/reasons: allow any non-whitespace, max 255
LooseString = Annotated[str, constr(min_length=1, max_length=255)]