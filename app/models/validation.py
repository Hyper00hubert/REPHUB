"""Validation data structures supporting Module 6 input checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List, Set


class ValidationSeverity(str, Enum):
    """Enumeration describing how severe a validation issue is."""

    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ValidationIssue:
    """Represents a single validation problem detected in user input."""

    field: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.WARNING


@dataclass
class ValidationReport:
    """Aggregates validation issues and metadata about invalid inputs."""

    issues: List[ValidationIssue] = field(default_factory=list)
    invalid_items: Set[str] = field(default_factory=set)
    invalid_fields: dict[str, Set[str]] = field(default_factory=dict)

    def add_issue(
        self,
        field: str,
        message: str,
        severity: ValidationSeverity = ValidationSeverity.WARNING,
    ) -> None:
        """Append a new validation issue to the report."""

        self.issues.append(ValidationIssue(field=field, message=message, severity=severity))

    def extend(self, issues: Iterable[ValidationIssue]) -> None:
        """Add pre-existing issues to the report."""

        self.issues.extend(issues)

    def mark_invalid_item(self, item_name: str) -> None:
        """Remember that the provided ration item should be ignored by calculators."""

        self.invalid_items.add(item_name)

    def mark_invalid_field(self, item_name: str, field_key: str) -> None:
        """Register a nutrient field that cannot be used in calculations."""

        bucket = self.invalid_fields.setdefault(item_name, set())
        bucket.add(field_key)

    def messages(self) -> List[str]:
        """Return validation issue messages for presentation to the user."""

        return [issue.message for issue in self.issues]

    def has_errors(self) -> bool:
        """Return ``True`` when at least one blocking error was detected."""

        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
