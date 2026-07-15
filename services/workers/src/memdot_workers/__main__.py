"""Workers health entrypoint."""

import uvicorn

from memdot_workers.app import create_app
from memdot_workers.settings import WorkersSettings


def main() -> None:
    settings = WorkersSettings()
    uvicorn.run(
        create_app(settings),
        host=settings.health_host,
        port=settings.health_port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
