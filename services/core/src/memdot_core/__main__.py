"""Core service entrypoint."""

import uvicorn

from memdot_core.app import create_app
from memdot_core.settings import CoreSettings


def main() -> None:
    settings = CoreSettings()
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
