import argparse
import logging
import os
import sys
import traceback
from typing import Literal, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from voice import KokoroTTS


class VoiceMCP:
    def __init__(
        self, lang: Optional[str], voice: Optional[str], sample_rate: Optional[int]
    ):
        self._setup_logging()

        self.lang = lang
        self.voice = voice
        self.sample_rate = sample_rate

        self.tts = None
        self.mcp = FastMCP(name="Voice TTS MCP", version="1.0.0", request_timeout=30)

        self._init_tts()
        self._register_tools()
        logging.info("Gmail MCP initialized")

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    def _init_tts(self):
        logging.info("Initializing TTS engine")
        self.tts = KokoroTTS(
            lang=self.lang, voice=self.voice, sample_rate=self.sample_rate
        )

    def _register_tools(self):
        logging.info("Registering tools")

        @self.mcp.tool("voice")
        def play_audio(
            text: str,
            speed: float = 1.0,
            chunk_size: int = 200,
            lang: Optional[
                Literal["us", "uk", "es", "fr", "hi", "it", "jp", "pt", "zh"]
            ] = None,
            voice: Optional[
                Literal[
                    "am_michael",
                    "bm_george",
                    "af_sky",
                    "af_nicole",
                    "af_sarah",
                    "bf_emma",
                    "af_bella",
                    "bf_isabella",
                    "am_adam",
                ]
            ] = None,
            ctx: Context = None,
        ):
            """
            Generate speech from the provided text and play it.

            Args:
                text: Text to convert to speech
                speed: Playback speed multiplier (1.0 = normal speed)
                chunk_size: Maximum size of each text chunk
                lang: Language code to use (overrides default if specified)
                voice: Voice to use (overrides default if specified)
                ctx: MCP context object

            Returns:
                Success message
            """
            try:
                if ctx:
                    ctx.info(f"Generating speech for text ({len(text)} characters)")

                self.tts.play_audio(
                    text=text,
                    speed=speed,
                    chunk_size=chunk_size,
                    lang=lang,
                    voice=voice,
                )

                if ctx:
                    ctx.info("Audio playback completed")
                    return {
                        "success": True,
                        "message": (
                            f"Played audio: {text[:30]}..." if len(text) > 30 else text
                        ),
                    }
                else:
                    return {"success": True, "message": f"Played audio: {text[:30]}..."}
            except Exception as e:
                error_msg = f"Error playing audio: {str(e)}"
                logging.error(error_msg)

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

    def run(self):
        try:
            logging.info("Starting Voice TTS MCP Server")
            self.mcp.run(transport="stdio")
        except Exception as e:
            logging.error(f"Fatal error occurred: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Voice MCP Server")
    parser.add_argument(
        "--lang",
        type=str,
        default=os.environ.get("VOICE_LANG", "us"),
        help="Language code (default: us, env: VOICE_LANG)",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default=os.environ.get("VOICE_NAME"),
        help="Voice name (env: VOICE_NAME)",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=int(os.environ.get("VOICE_SAMPLE_RATE", 24000)),
        help="Sample rate (env: VOICE_SAMPLE_RATE)",
    )

    args = parser.parse_args()
    server = VoiceMCP(lang=args.lang, voice=args.voice, sample_rate=args.sample_rate)
    server.run()


if __name__ == "__main__":
    try:
        logging.info("Initializing Voice MCP server")
        main()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal. Gracefully shutting down...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error occurred during initialization: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
