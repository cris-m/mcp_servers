import argparse
import logging
import sys
import traceback

from mcp.server.fastmcp import Context, FastMCP
from timer_manager import TimeManager


class TimeMCP:
    def __init__(self, local_timezone=None):
        self.local_timezone = local_timezone or "UTC"

        self._setup_logging()
        self._init_time_manager()

        self.mcp = FastMCP(name="Time MCP Server", version="1.0.0")
        self.register_tools()

        logging.info("Time MCP initialized")

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

    def _init_time_manager(self):
        try:
            self.time_manager = TimeManager(local_timezone=self.local_timezone)
            self.logger.info(
                f"TimeManager initialized with timezone: {self.local_timezone}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize TimeManager: {e}")
            raise

    def register_tools(self):
        """
        Register time-related tools with the FastMCP server.
        """
        logging.info("Registering tools")

        @self.mcp.tool("time_current")
        def get_current_time(timezone: str = None, ctx: Context = None):
            """
            Get the current time.

            :param timezone: Optional timezone (defaults to local timezone)
            :param ctx: FastMCP context
            :return: Current time information
            """
            if ctx:
                ctx.info(f"Current time request - Timezone: {timezone}")

            try:
                target_timezone = timezone or self.local_timezone
                result = self.time_manager.get_current_time(target_timezone)

                if ctx:
                    ctx.info(f"Current time retrieved for {target_timezone}")

                return result
            except Exception as e:
                if ctx:
                    ctx.error(f"Error getting current time for {timezone}: {e}")
                return {"error": str(e)}

        @self.mcp.tool("time_word_clock")
        def word_clock(timezone: str = None, precision: int = 1, ctx: Context = None):
            """
            Get the word clock representation of time.

            :param timezone: Optional timezone (defaults to local timezone)
            :param precision: Precision in minutes (default 1)
            :param ctx: FastMCP context
            :return: Word clock time representation
            """
            if ctx:
                ctx.info(
                    f"Word clock request - Timezone: {timezone}, Precision: {precision}"
                )

            try:
                target_timezone = timezone or self.local_timezone
                result = self.time_manager.word_clock(target_timezone, precision)

                if ctx:
                    ctx.info(f"Word clock retrieved for {target_timezone}")

                return result
            except Exception as e:
                if ctx:
                    ctx.error(f"Error getting word clock for {timezone}: {e}")
                return {"error": str(e)}

        @self.mcp.tool("time_convert")
        def convert_time(
            source_timezone: str,
            time_str: str,
            target_timezone: str,
            ctx: Context = None,
        ):
            """
            Convert time between different timezones.

            :param source_timezone: Source timezone
            :param time_str: Time to convert (HH:MM format)
            :param target_timezone: Target timezone
            :param ctx: FastMCP context
            :return: Time conversion details
            """
            if ctx:
                ctx.info(
                    f"Time conversion request - "
                    f"Source: {source_timezone}, "
                    f"Time: {time_str}, "
                    f"Target: {target_timezone}"
                )

            try:
                result = self.time_manager.convert_time(
                    source_timezone, time_str, target_timezone
                )

                if ctx:
                    ctx.info(
                        f"Time converted from {source_timezone} to {target_timezone}"
                    )

                return result
            except Exception as e:
                if ctx:
                    ctx.error(
                        f"Error converting time from {source_timezone} "
                        f"to {target_timezone}: {e}"
                    )
                return {"error": str(e)}

        @self.mcp.tool("time_timezone_list")
        def list_timezones(ctx: Context = None):
            """
            List all available timezones.

            :param ctx: FastMCP context
            :return: List of timezone strings
            """
            if ctx:
                ctx.info("Timezone list request")

            try:
                timezones = self.time_manager.list_timezones()

                if ctx:
                    ctx.info(f"Retrieved {len(timezones)} timezones")

                return {"timezones": timezones, "count": len(timezones)}
            except Exception as e:
                if ctx:
                    ctx.error(f"Error listing timezones: {e}")
                return {"error": str(e)}

        @self.mcp.tool("time_timezone_validate")
        def validate_timezone(timezone: str, ctx: Context = None):
            """
            Validate if a given timezone is valid.

            :param timezone: Timezone string to validate
            :param ctx: FastMCP context
            :return: Validation result
            """
            if ctx:
                ctx.info(f"Timezone validation request - Timezone: {timezone}")

            try:
                result = self.time_manager.validate_timezone(timezone)

                if ctx:
                    ctx.info(
                        f"Timezone validation result for {timezone}: "
                        f"{'Valid' if result['valid'] else 'Invalid'}"
                    )

                return result
            except Exception as e:
                if ctx:
                    ctx.error(f"Error validating timezone {timezone}: {e}")
                return {"error": str(e)}

    def run(self):
        """
        Start the TimeMCP server.
        """
        try:
            self.logger.info("Starting TimeMCP server...")
            self.mcp.run(transport="stdio")
            self.logger.info("TimeMCP server started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start TimeMCP server: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description="Time MCP Server")
    parser.add_argument(
        "-t", "--timezone", default="UTC", help="Local timezone (default: UTC)"
    )

    args = parser.parse_args()

    time_mcp = TimeMCP(local_timezone=args.timezone)
    time_mcp.run()


if __name__ == "__main__":
    try:
        logging.info("Initializing Time MCP server")
        main()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal. Gracefully shutting down...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error occurred during initialization: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
