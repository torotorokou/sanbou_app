"""
Plan worker: simple background worker template.
"""
import logging
import time
import os

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("plan_worker")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))  # seconds


def process_task():
    """
    Process a single task.
    TODO: Implement actual task processing logic.
    """
    logger.info("Processing task...")
    # Add your task processing logic here
    time.sleep(1)
    logger.info("Task completed")


def main():
    """Main worker loop."""
    logger.info("Plan worker started", extra={"poll_interval": POLL_INTERVAL})

    while True:
        try:
            process_task()
        except Exception as e:
            logger.error(f"Error processing task: {e}")
        
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

