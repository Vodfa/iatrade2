import logging
import threading
from dataclasses import dataclass, field
from time import time
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class AutoTradeBrowserConfig:
    demo_url: str = "https://testnet.binance.vision/"
    launch_on_start: bool = True


@dataclass
class AutoTradePanelState:
    selected_pairs: list[str] = field(default_factory=lambda: ["BTC/USDT"])
    quote_currencies: list[str] = field(default_factory=lambda: ["USDT"])
    extra_filters: list[str] = field(default_factory=list)
    timer_interval_sec: int = 60
    browser: AutoTradeBrowserConfig = field(default_factory=AutoTradeBrowserConfig)
    enabled: bool = False
    last_run_ts: int | None = None
    next_run_ts: int | None = None


class AutoTradeManager:
    """
    Lightweight scheduler for auto-trade support in the API layer.

    This does not place orders directly. It orchestrates periodic runs and keeps
    track of panel preferences so clients can build richer trading workflows.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._state = AutoTradePanelState()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "selected_pairs": self._state.selected_pairs,
                "quote_currencies": self._state.quote_currencies,
                "extra_filters": self._state.extra_filters,
                "timer_interval_sec": self._state.timer_interval_sec,
                "browser": {
                    "demo_url": self._state.browser.demo_url,
                    "launch_on_start": self._state.browser.launch_on_start,
                },
                "enabled": self._state.enabled,
                "last_run_ts": self._state.last_run_ts,
                "next_run_ts": self._state.next_run_ts,
            }

    def update_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._state.selected_pairs = payload["selected_pairs"]
            self._state.quote_currencies = payload["quote_currencies"]
            self._state.extra_filters = payload["extra_filters"]
            self._state.timer_interval_sec = payload["timer_interval_sec"]
            browser = payload["browser"]
            self._state.browser = AutoTradeBrowserConfig(
                demo_url=browser["demo_url"],
                launch_on_start=browser["launch_on_start"],
            )
            if self._state.enabled:
                self._state.next_run_ts = int(time()) + self._state.timer_interval_sec
        return self.get_state()

    def _launch_browser(self) -> None:
        if not self._state.browser.launch_on_start:
            return
        try:
            import webbrowser

            webbrowser.open(self._state.browser.demo_url, new=2)
        except Exception as exc:
            logger.warning("AutoTrade browser launch failed: %s", exc)

    def _run_cycle(self) -> None:
        with self._lock:
            now = int(time())
            self._state.last_run_ts = now
            self._state.next_run_ts = now + self._state.timer_interval_sec
            logger.info(
                "AutoTrade cycle executed | pairs=%s quotes=%s filters=%s",
                ",".join(self._state.selected_pairs),
                ",".join(self._state.quote_currencies),
                ",".join(self._state.extra_filters),
            )

    def _scheduler(self) -> None:
        while not self._stop_event.wait(self._state.timer_interval_sec):
            if not self._state.enabled:
                continue
            self._run_cycle()

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self._state.enabled:
                return self.get_state()
            self._state.enabled = True
            now = int(time())
            self._state.next_run_ts = now + self._state.timer_interval_sec
            self._stop_event.clear()
            if not self._thread or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._scheduler, name="AutoTradeScheduler")
                self._thread.daemon = True
                self._thread.start()
            self._launch_browser()
        return self.get_state()

    def stop(self) -> dict[str, Any]:
        with self._lock:
            self._state.enabled = False
            self._state.next_run_ts = None
            self._stop_event.set()
        return self.get_state()

    def run_now(self) -> dict[str, Any]:
        self._run_cycle()
        return self.get_state()
