from pathlib import Path

from alembic import command
from alembic.config import Config


def main() -> None:
    config_path = Path(__file__).with_name("alembic.ini")
    command.upgrade(Config(str(config_path)), "head")


if __name__ == "__main__":
    main()