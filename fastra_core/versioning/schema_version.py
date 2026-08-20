from dataclasses import dataclass
from enum import Enum

class VersionCompatibility(Enum):
    COMPATIBLE = "compatible"
    NEEDS_MIGRATION = "needs_migration"
    INCOMPATIBLE = "incompatible"

@dataclass
class SchemaVersion:
    major: int
    minor: int
    patch: int

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, s: str) -> "SchemaVersion":
        parts = s.split(".")
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))

    def is_compatible_with(self, other: "SchemaVersion") -> VersionCompatibility:
        if self.major != other.major:
            return VersionCompatibility.INCOMPATIBLE
        if self.minor != other.minor:
            return VersionCompatibility.NEEDS_MIGRATION
        return VersionCompatibility.COMPATIBLE
