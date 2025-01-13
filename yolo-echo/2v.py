#!/usr/bin/env python3
"""
A simple, expert-level Python TCP server that always returns 'yolo' to any client request.
Demonstrates best practices, including:
- Only using built-in standard libraries
- Graceful shutdown handling
- Logging
- Clear docstrings
"""

import socket
import threading
import logging
import signal
import sys
from typing import Tuple

class YoloEchoServer:
    """
    A TCP server that returns 'yolo' to any connected client.

    Attributes:
        host (str): The hostname or IP address on which the server listens.
        port (int): The TCP port number on which the server listens.
        backlog (int): The maximum length to which the queue of pending connections may grow.
        _server_socket (socket.socket): The main server socket that listens for new connections.
        _running (bool): A flag indicating whether the server is running.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5000, backlog: int = 5) -> None:
        """
        Initialize the YoloEchoServer with specified host, port, and backlog.

        Args:
            host (str, optional): Hostname or IP address for the server. Defaults to "127.0.0.1".
            port (int, optional): Port number to listen on. Defaults to 5000.
            backlog (int, optional): Maximum pending connections. Defaults to 5.
        """
        self.host = host
        self.port = port
        self.backlog = backlog
        self._running = False
        self._server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """
        Set up a basic configuration for logging.
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def _bind_socket(self) -> None:
        """
        Bind the server socket to the specified host and port.
        """
        try:
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(self.backlog)
            self._server_socket.settimeout(1.0)  # Non-blocking accept with a short timeout
            logging.info("Server bound to %s:%d", self.host, self.port)
        except socket.error as err:
            logging.error("Failed to bind socket: %s", err)
            sys.exit(1)

    def run(self) -> None:
        """
        Run the main server loop, accepting and handling new client connections.
        """
        self._bind_socket()
        self._running = True
        logging.info("Server is now running. Press Ctrl+C to stop.")

        while self._running:
            try:
                client_sock, client_addr = self._server_socket.accept()
            except socket.timeout:
                # Loop around to check if we're still running
                continue
            except OSError as err:
                # Socket likely closed during shutdown
                logging.debug("Server socket accept interrupted: %s", err)
                break

            # Handle client in a separate thread
            client_thread = threading.Thread(
                target=self._handle_client,
                args=(client_sock, client_addr),
                daemon=True
            )
            client_thread.start()

        self._server_socket.close()
        logging.info("Server has been shut down.")

    def shutdown(self) -> None:
        """
        Signal the server to shut down gracefully.
        """
        self._running = False

    def _handle_client(self, client_sock: socket.socket, client_addr: Tuple[str, int]) -> None:
        """
        Handle a single client connection by sending 'yolo' and closing the connection.

        Args:
            client_sock (socket.socket): The client socket to communicate with.
            client_addr (Tuple[str, int]): The client's address (IP, port).
        """
        logging.info("Client connected: %s:%d", client_addr[0], client_addr[1])
        try:
            # Send 'yolo' to the client
            response = b"yolo"
            client_sock.sendall(response)
            logging.debug("Sent response %r to client %s:%d", response, client_addr[0], client_addr[1])
        except (socket.error, ConnectionError) as err:
            logging.error("Error sending data to client %s:%d - %s", client_addr[0], client_addr[1], err)
        finally:
            client_sock.close()
            logging.info("Connection closed: %s:%d", client_addr[0], client_addr[1])


def _handle_signals(server_instance: YoloEchoServer) -> None:
    """
    Set up signal handlers to gracefully stop the server on SIGINT or SIGTERM.

    Args:
        server_instance (YoloEchoServer): The server instance to shutdown.
    """
    def shutdown_signal_handler(signum, frame):
        logging.info("Received shutdown signal (%d). Shutting down...", signum)
        server_instance.shutdown()

    signal.signal(signal.SIGINT, shutdown_signal_handler)
    signal.signal(signal.SIGTERM, shutdown_signal_handler)


def main() -> None:
    """
    Entry point for running the YoloEchoServer.
    """
    server = YoloEchoServer(host="127.0.0.1", port=5000, backlog=5)
    _handle_signals(server)

    try:
        server.run()
    finally:
        # Ensure shutdown is called in any exit scenario
        server.shutdown()


if __name__ == "__main__":
    main()
