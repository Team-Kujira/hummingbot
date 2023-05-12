import asyncio
import time
from logging import DEBUG, ERROR
from typing import Any, Dict, List

import jsonpickle

from hummingbot.client.hummingbot_application import HummingbotApplication
from hummingbot.connector.gateway.clob_spot.gateway_clob_spot import GatewayCLOBSPOT
from hummingbot.core.clock import Clock
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


# noinspection DuplicatedCode
class KujiraAPIDataSourceTester(ScriptStrategyBase):

    def __init__(self):
        try:
            self._log(DEBUG, """__init__... start""")

            super().__init__()

            self._can_run: bool = True
            self._is_busy: bool = False
            self._refresh_timestamp: int = 0

            self._configuration = {
                "markets": {
                    "kujira_kujira_testnet": [  # Only one market can be used for now
                        # "KUJI-DEMO",  # "kujira1suhgf5svhu4usrurvxzlgn54ksxmn8gljarjtxqnapv8kjnp4nrsqq4jjh"
                        "KUJI-USK",   # "kujira1wl003xxwqltxpg5pkre0rl605e406ktmq5gnv0ngyjamq69mc2kqm06ey6"
                        # "DEMO-USK",   # "kujira14sa4u42n2a8kmlvj3qcergjhy6g9ps06rzeth94f2y6grlat6u6ssqzgtg"
                    ]
                },
                "strategy": {
                    "tick_interval": 59,
                    "run_only_once": False
                },
                "logger": {
                    "level": "DEBUG"
                }
            }
        finally:
            self._log(DEBUG, """__init__... end""")

    def get_markets_definitions(self) -> Dict[str, List[str]]:
        return self._configuration["markets"]

    # noinspection PyAttributeOutsideInit
    async def initialize(self, start_command):
        try:
            self._log(DEBUG, """_initialize... start""")

            self.logger().setLevel(self._configuration["logger"].get("level", "INFO"))

            await super().initialize(start_command)

            self.initialized = False

            self._connector_id = next(iter(self._configuration["markets"]))

            # noinspection PyTypeChecker
            self._connector: GatewayCLOBSPOT = self.connectors[self._connector_id]

            self.initialized = True
        except Exception as exception:
            self._handle_error(exception)

            HummingbotApplication.main_application().stop()
        finally:
            self._log(DEBUG, """_initialize... end""")

    async def on_tick(self):
        if (not self._is_busy) and (not self._can_run):
            HummingbotApplication.main_application().stop()

        # noinspection PyUnresolvedReferences
        if self._is_busy or (self._refresh_timestamp > self.current_timestamp):
            return

        try:
            self._log(DEBUG, """on_tick... start""")

            self._is_busy = True
        except Exception as exception:
            self._handle_error(exception)
        finally:
            waiting_time = self._calculate_waiting_time(self._configuration["strategy"]["tick_interval"])

            # noinspection PyAttributeOutsideInit
            self._refresh_timestamp = waiting_time + self.current_timestamp
            self._is_busy = False

            self._log(DEBUG, f"""Waiting for {waiting_time}s.""")

            self._log(DEBUG, """on_tick... end""")

            if self._configuration["strategy"]["run_only_once"]:
                HummingbotApplication.main_application().stop()

    def stop(self, clock: Clock):
        asyncio.get_event_loop().run_until_complete(self.async_stop(clock))

    async def async_stop(self, clock: Clock):
        try:
            self._log(DEBUG, """_stop... start""")

            self._can_run = False

            super().stop(clock)
        finally:
            self._log(DEBUG, """_stop... end""")

    @staticmethod
    def _calculate_waiting_time(number: int) -> int:
        current_timestamp_in_milliseconds = int(time.time() * 1000)
        result = number - (current_timestamp_in_milliseconds % number)

        return result

    async def retry_async_with_timeout(self, function, *arguments, number_of_retries=3, timeout_in_seconds=60, delay_between_retries_in_seconds=0.5):
        for retry in range(number_of_retries):
            try:
                return await asyncio.wait_for(function(*arguments), timeout_in_seconds)
            except asyncio.TimeoutError:
                self._log(ERROR, f"TimeoutError in the attempt {retry+1} of {number_of_retries}.", True)
            except Exception as exception:
                message = f"""ERROR in the attempt {retry+1} of {number_of_retries}: {type(exception).__name__} {str(exception)}"""
                self._log(ERROR, message, True)
            await asyncio.sleep(delay_between_retries_in_seconds)
        raise Exception(f"Operation failed with {number_of_retries} attempts.")

    def _log(self, level: int, message: str, *args, **kwargs):
        # noinspection PyUnresolvedReferences
        message = f"""{message}"""

        self.logger().log(level, message, *args, **kwargs)

    def _handle_error(self, exception: Exception):
        message = f"""ERROR: {type(exception).__name__} {str(exception)}"""
        self._log(ERROR, message, True)

    @staticmethod
    def _dump(target: Any):
        try:
            return jsonpickle.encode(target, unpicklable=True, indent=2)
        except (Exception,):
            return target
