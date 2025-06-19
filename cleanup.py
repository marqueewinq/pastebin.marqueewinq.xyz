import logging
import os
from datetime import datetime, timedelta


async def cleanup_old_pastes(
    data_dir: str,
    max_age_hours: int = 24,
    logger: logging.Logger = logging.getLogger("pastebin"),
):
    """
    Clean up pastes that are older than 24 hours.

    This function:
    1. Scans the pastes directory for all paste files
    2. Checks the creation timestamp of each paste
    3. Deletes pastes older than 24 hours
    4. Logs the cleanup results
    """
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    deleted_count = 0

    try:
        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)

            # Skip if not a file
            if not os.path.isfile(file_path):
                continue

            # Get file creation time
            creation_time = datetime.fromtimestamp(os.path.getctime(file_path))

            # Delete if older than 24 hours
            if creation_time < cutoff_time:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.debug(
                        f"\tDeleted old paste: {filename} (created: {creation_time})"
                    )
                except OSError as e:
                    logger.error(f"\tFailed to delete {filename}: {e}")

        if deleted_count > 0:
            logger.info(f"\tCleanup completed: deleted {deleted_count} old pastes")
        else:
            logger.info("\tNo old pastes to delete")

    except Exception as e:
        logger.error(f"\tError during cleanup: {e}")
