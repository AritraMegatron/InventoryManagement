from __future__ import annotations

import os
from pathlib import Path
import asyncio
from dotenv import load_dotenv
from nicegui import app, ui


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / 'app' / 'assets'
LOGO_FILE = ASSETS_DIR / 'inventide_logo.png'
ENV_FILE = BASE_DIR / '.env'


# Load environment variables before importing pages or OpenAI services.
load_dotenv(
    dotenv_path=ENV_FILE,
    override=True,
)


from app.pages import command_center  # noqa: E402,F401
from app.pages import demand_inventory  # noqa: E402,F401
from app.pages import network_intelligence  # noqa: E402,F401
from app.pages import outlet_intelligence  # noqa: E402,F401
from app.pages import product_innovation  # noqa: E402,F401


app.add_static_files(
    '/assets',
    str(ASSETS_DIR),
)


@ui.page('/')
def index() -> None:
    ui.navigate.to(
        '/command-center'
    )


storage_secret = os.getenv(
    'NICEGUI_STORAGE_SECRET',
    'vesper-local-development-secret-change-before-deployment',
)


@app.on_startup
async def configure_asyncio_error_handler() -> None:
    loop = asyncio.get_running_loop()
    previous_handler = loop.get_exception_handler()

    def handle_asyncio_exception(
        event_loop: asyncio.AbstractEventLoop,
        context: dict,
    ) -> None:
        exception = context.get('exception')

        if (
            isinstance(exception, ConnectionResetError)
            and getattr(exception, 'winerror', None) == 10054
        ):
            return

        if previous_handler is not None:
            previous_handler(
                event_loop,
                context,
            )
        else:
            event_loop.default_exception_handler(
                context
            )

    loop.set_exception_handler(
        handle_asyncio_exception
    )


ui.run(
    title='Supply Chain Intelligence | Inventide',
    favicon=str(LOGO_FILE),
    reload=False,
    show=False,
    host='0.0.0.0',
    port=int(os.getenv('PORT', '8082')),
    storage_secret=storage_secret,
)