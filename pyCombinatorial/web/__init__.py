from __future__ import annotations

import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

__all__ = ["WebVisualizerServer", "web_app"]


class _QuietHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves the packaged web assets with minimal logging."""

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


class WebVisualizerServer:
    """Container for a running pyCombinatorial web visualizer server."""

    def __init__(
        self,
        server: ThreadingHTTPServer,
        thread: Optional[threading.Thread],
        url: str,
        directory: Path,
    ) -> None:
        self.server = server
        self.thread = thread
        self.url = url
        self.directory = directory

    @property
    def host(self) -> str:
        return str(self.server.server_address[0])

    @property
    def port(self) -> int:
        return int(self.server.server_address[1])

    def shutdown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def __repr__(self) -> str:
        return f"WebVisualizerServer(url={self.url!r}, directory={str(self.directory)!r})"


def _build_url(host: str, port: int) -> str:
    display_host = '127.0.0.1' if host in ('0.0.0.0', '::') else host
    return f'http://{display_host}:{port}/'



def web_app(
    host: str = '127.0.0.1',
    port: int = 8000,
    open_browser: bool = True,
    block: bool = True,
) -> WebVisualizerServer:
    """
    Launch the packaged pyCombinatorial web visualizer.

    Parameters
    ----------
    host : str, default='127.0.0.1'
        Network interface used by the local HTTP server.
    port : int, default=8000
        Port used by the local HTTP server. Use 0 for an ephemeral free port.
    open_browser : bool, default=True
        Open the default browser automatically.
    block : bool, default=True
        If True, keep the server in the foreground until interrupted.
        If False, run it in a daemon thread and return immediately.

    Returns
    -------
    WebVisualizerServer
        Object containing the server, thread handle, served directory, and URL.
    """

    web_dir = Path(__file__).resolve().parent
    index_html = web_dir / 'index.html'
    if not index_html.exists():
        raise FileNotFoundError(
            'The packaged web visualizer assets were not found. '
            'Reinstall pyCombinatorial ensuring package data is included.'
        )

    handler = partial(_QuietHandler, directory=str(web_dir))
    server = ThreadingHTTPServer((host, port), handler)
    actual_host, actual_port = server.server_address[:2]
    url = _build_url(str(actual_host), int(actual_port))
    app = WebVisualizerServer(server=server, thread=None, url=url, directory=web_dir)

    if open_browser:
        webbrowser.open(url)

    if block:
        print(f'pyCombinatorial web visualizer available at {url}')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            app.shutdown()
        return app

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    app.thread = thread
    return app
