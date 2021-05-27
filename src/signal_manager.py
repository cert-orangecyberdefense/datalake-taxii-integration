import signal


class SignalManager:
    """
    Listen to sigterm/sigint signal (via `kill -SIGTERM pid`) to toggle is_stop_requested
    """
    is_stop_requested = False

    def __init__(self):
        signal.signal(signal.SIGTERM, self.request_stop)
        signal.signal(signal.SIGINT, self.request_stop)

    def request_stop(self, _signum, _frame):
        self.is_stop_requested = True
