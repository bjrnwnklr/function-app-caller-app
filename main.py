import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name=__name__)


def main():
    logger.info("Hello from the external-caller-app!")


if __name__ == "__main__":
    main()
