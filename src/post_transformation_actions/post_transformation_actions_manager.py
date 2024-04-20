import logging

from src.config import Config


# delete comment about pylint after filling the function
# pylint: disable=unused-argument
def run_post_transformation_actions(config: Config) -> bool:
    """
    Run all required actions after data transformation.
    :param config: App configuration.
    :return: True if these actions succeeded and the app should be exited with success, False otherwise.
    """
    logging.info("Starting post transformation actions.")
    # Space to put any post transformation actions, such as copying the created files into another storage
    logging.info("Post transformation actions finished successfully.")
    return True
