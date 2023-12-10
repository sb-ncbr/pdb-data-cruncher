from dataclasses import dataclass, field
from enum import Enum


class IssueType(Enum):
    DATA_ITEM_ERROR = 0
    UNCATEGORIZED = 99

    def __str__(self):
        return self.name.lower()


@dataclass
class Issue:
    type: IssueType = IssueType.UNCATEGORIZED
    message: str = ""


@dataclass
class Diagnostics:
    issues: list[Issue] = field(default_factory=list)

    @property
    def total_issues(self):
        return len(self.issues)

    # pylint: disable=redefined-builtin
    def add_issue(self, type: IssueType, msg: str) -> None:
        self.issues.append(Issue(type=type, message=msg))
