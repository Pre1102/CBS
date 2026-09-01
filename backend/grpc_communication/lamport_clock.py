import threading

class LamportClock:
    """
    Thread-safe implementation of Lamport Logical Clock for ordering distributed events.
    Follows Lamport's rules:
      1. Increment clock before local events and before sending a message.
      2. Upon receiving a message with timestamp T, update clock = max(local_clock, T) + 1.
    """
    def __init__(self, initial_time: int = 0):
        self._time = initial_time
        self._lock = threading.Lock()

    def increment(self) -> int:
        """
        Increments local clock by 1.
        Called on internal events and before sending distributed messages.
        """
        with self._lock:
            self._time += 1
            return self._time

    def update(self, received_time: int) -> int:
        """
        Updates local clock upon receiving a remote message timestamp.
        Sets clock = max(local_clock, received_time) + 1.
        """
        with self._lock:
            self._time = max(self._time, received_time) + 1
            return self._time

    def get_time(self) -> int:
        """
        Returns current value of the Lamport logical clock.
        """
        with self._lock:
            return self._time
