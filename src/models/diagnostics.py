import logging
from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class Diagnostics:
    """
    Class for collecting issues with data processing or other task, that are not critical issues
    and do not require the working of current function to be stopped, but still need to be logged
    or handled in some way at the end.
    """

    issue_messages: list[str] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        """
        Gets the number of issues collected.
        :return: Number of issues collected.
        """
        return len(self.issue_messages)

    def add(self, issue_message: str) -> None:
        """
        Adds given issue message to the diagnostics.
        :param issue_message: Message describing the issue (for logging purposes).
        """
        self.issue_messages.append(issue_message)

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
            for issue_message in self.issue_messages:
                logging.info("%s: %s", line_start_info, issue_message)
        else:
            logging.debug("%s finished with no issues", line_start_info)
