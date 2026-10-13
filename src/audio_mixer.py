from array import array
import queue
import threading

import discord


FRAME_SIZE = 3840  # 20 ms of 48 kHz, stereo, signed 16-bit PCM
SAMPLE_COUNT = FRAME_SIZE // 2


class _AudioLayer:
    """Reads one Discord audio source on a worker thread."""

    def __init__(self, source: discord.AudioSource, volume: float):
        self.source = source
        self.volume = max(0.0, min(float(volume), 2.0))
        self.frames = queue.Queue(maxsize=5)
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._produce, daemon=True)

    def start(self):
        self.thread.start()

    def _produce(self):
        try:
            while not self.stop_event.is_set():
                frame = self.source.read()
                if not frame:
                    break

                # Backpressure prevents FFmpeg from racing ahead and buffering
                # an entire track in memory.
                while not self.stop_event.is_set():
                    try:
                        self.frames.put(frame, timeout=0.1)
                        break
                    except queue.Full:
                        continue
        except Exception as exc:
            print(f"Audio layer read failed: {exc}")
        finally:
            # Notify the mixer when this source reaches EOF.
            while not self.stop_event.is_set():
                try:
                    self.frames.put(None, timeout=0.1)
                    break
                except queue.Full:
                    continue
            try:
                self.source.cleanup()
            except Exception:
                pass

    def stop(self):
        self.stop_event.set()
        try:
            self.source.cleanup()
        except Exception:
            pass


class LayeredAudioSource(discord.AudioSource):
    """Mix named PCM layers into the one stream Discord expects."""

    def __init__(self):
        self._layers = {}
        self._lock = threading.RLock()
        self._closed = False

    @property
    def closed(self):
        return self._closed

    def add(self, name: str, source: discord.AudioSource, volume: float = 1.0):
        layer = _AudioLayer(source, volume)
        with self._lock:
            if self._closed:
                raise RuntimeError("This audio mixer has been closed.")
            previous = self._layers.get(name)
            self._layers[name] = layer

        if previous is not None:
            previous.stop()
        layer.start()

    def remove(self, name: str) -> bool:
        with self._lock:
            layer = self._layers.pop(name, None)
        if layer is None:
            return False
        layer.stop()
        return True

    def stop_all(self):
        with self._lock:
            layers = list(self._layers.values())
            self._layers.clear()
        for layer in layers:
            layer.stop()

    def read(self) -> bytes:
        # Discord requests a frame every 20 ms. If a source is waiting on the
        # network, that layer contributes silence rather than blocking voice.
        mixed = array("h", [0]) * SAMPLE_COUNT
        with self._lock:
            layers = list(self._layers.items())

        for name, layer in layers:
            try:
                frame = layer.frames.get_nowait()
            except queue.Empty:
                continue

            if frame is None:
                with self._lock:
                    if self._layers.get(name) is layer:
                        self._layers.pop(name, None)
                layer.stop()
                continue

            if len(frame) < FRAME_SIZE:
                frame = frame.ljust(FRAME_SIZE, b"\x00")
            elif len(frame) > FRAME_SIZE:
                frame = frame[:FRAME_SIZE]

            samples = array("h")
            samples.frombytes(frame)
            volume = layer.volume
            for index, sample in enumerate(samples):
                value = mixed[index] + int(sample * volume)
                mixed[index] = max(-32768, min(32767, value))

        # A silent frame keeps the shared Discord stream ready for later layers.
        return mixed.tobytes()

    def cleanup(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self.stop_all()
