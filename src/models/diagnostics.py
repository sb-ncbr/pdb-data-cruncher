import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class IssueType(Enum):
    """
    Type of issue.
    """

    DATA_ITEM_ERROR = 0
    UNCATEGORIZED = 99

    def __str__(self) -> str:
        """
        Overrides default transformation to string. Returns the name of issue type in lowercase.
        :return: Name of issue type in lowercase.
        """
        return self.name.lower()


@dataclass
class Issue:
    """
    Class holding information about one issue.
    """

    type: IssueType = IssueType.UNCATEGORIZED
    message: str = ""


@dataclass
class Diagnostics:
    """
    Class for collecting issues with data processing or other task, that are not critical issues
    and do not require the working of current function to be stopped, but still need to be logged
    or handled in some way at the end.
    """

    issues: list[Issue] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        """
        Gets the number of issues collected.
        :return: Number of issues collected.
        """
        return len(self.issues)

    # pylint: disable=redefined-builtin
    def add_issue(self, type: IssueType, msg: str) -> None:
        """
        Creates new issue from given information, and adds it to diagnostics.
        :param type: Type of issue.
        :param msg: Message describing the issue (for logging purposes).
        """
        self.issues.append(Issue(type=type, message=msg))

    def process_into_logging(self, action_name: str, pdb_id: Optional[str]) -> None:
        """
        Takes issues collected and outputs them into logging. One logging warning if there are any issues,
        followed by logging info with details about them. Only prints success without issues on debug level.
        :param action_name: Name of the action that will be put into the logs.
        :param pdb_id: PDB ID of protein that was being processed during diagnostic collection.
        """
        line_start_info = f"[{pdb_id}] {action_name}" if pdb_id else action_name
        if self.total_issues > 0:
            logging.warning(
                "%s finished with %s non-critical issues that may require attention.",
                line_start_info,
                self.total_issues,
            )
            for issue in self.issues:
                logging.info("%s: %s", line_start_info, issue.message)
        else:
            logging.debug("%s finished with no issues", line_start_info)
