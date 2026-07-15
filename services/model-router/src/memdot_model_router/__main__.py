"""Model-router entrypoint."""

import uvicorn

from memdot_model_router.app import create_app
from memdot_model_router.settings import ModelRouterSettings


def main() -> None:
    settings = ModelRouterSettings()
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
