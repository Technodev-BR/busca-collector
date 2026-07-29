from __future__ import annotations

from collector.core.runner import run
from collector.setup import setup


def main() -> None:
    pipeline = setup()
    run(pipeline.run)


if __name__ == "__main__":
    main()
