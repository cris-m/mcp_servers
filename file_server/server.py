import argparse
import logging
import os
import sys
import traceback
from typing import Optional

from dotenv import load_dotenv
from files import FileManager
from mcp.server.fastmcp import Context, FastMCP


class FileMCP:
    def __init__(
        self,
        root_folders,
        restricted_folders=None,
        restricted_files=None,
        ignore_patterns=None,
        include_defaults=True,
    ):
        self._setup_logging()

        self.file_manager = FileManager(
            root_folders=root_folders,
            restricted_folders=restricted_folders,
            restricted_files=restricted_files,
            ignore_patterns=ignore_patterns,
            include_defaults=include_defaults,
        )

        self.mcp = FastMCP(name="FileMCP", version="1.0.0", request_timeout=300)
        logging.info("Gmail MCP initialized")

        self._register_resources()
        self._register_tools()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    def _register_resources(self):
        """Register resources with the MCP server."""
        logging.info("Registering resources with MCP server")

        @self.mcp.resource("file://{path}")
        def get_file_content(path: str) -> str:
            """
            Get file content as a resource.

            Args:
                path: Path to the file
                ctx: MCP context object

            Return:
                File content as string
            """
            logging.info(f"Resource request: file://{path}")

            try:
                content = self.file_manager.read_file(path)
                logging.info(f"Successfully read file: {path} ({len(content)} bytes)")
                return content
            except Exception as e:
                error_msg = f"Error reading file: {str(e)}"
                return error_msg

        @self.mcp.resource("file-list://{path}/{depth}")
        def get_file_list(path: str, depth: str) -> str:
            """
            Get list of files in a directory as a resource.

            Args:
                path: Directory path to list files from
                depth: Depth of directory traversal (as string)
                ctx: MCP context object

            Return:
                List of files as string
            """
            logging.info(f"Resource request: file-list://{path}/{depth}")

            try:
                depth_int = int(depth)
                files = self.file_manager.list_files(path, depth_int)
                logging.info(f"Listed {len(files)} files in {path}")
                return "\n".join(files)
            except Exception as e:
                error_msg = f"Error listing files: {str(e)}"
                return error_msg

        @self.mcp.resource("file-info://{path}")
        def get_file_info(path: str) -> str:
            """
            Get file information as a resource.

            Args:
                path: Path to the file
                ctx: MCP context object

            Return:
                File information as string
            """
            logging.info(f"Resource request: file-info://{path}")

            try:
                info = self.file_manager.get_file_info(path)
                logging.info(f"Retrieved file info for {path}")
                return "\n".join([f"{key}: {value}" for key, value in info.items()])
            except Exception as e:
                error_msg = f"Error getting file info: {str(e)}"
                logging.error(f"{error_msg} - {path}")
                return error_msg

    def _register_tools(self):
        """Register tools with the MCP server."""
        logging.info("Registering tools with MCP server")

        @self.mcp.tool()
        def list_files(
            path: Optional[str] = None, depth: int = 1, ctx: Context = None
        ) -> list:
            """
            List files in the given path up to specified depth.

            Args:
                path: Path to list files from (defaults to first root)
                depth: Depth of directory traversal
                ctx: MCP context object

            Return:
                List of file paths
            """
            logging.info(f"Tool call: list_files(path={path}, depth={depth})")
            if ctx:
                ctx.info(
                    f"Listing files in {'root folders' if path is None else path} with depth {depth}"
                )

            try:
                files = self.file_manager.list_files(path, depth)
                logging.info(f"Listed {len(files)} files in {path or 'default root'}")
                if ctx:
                    ctx.info(f"Found {len(files)} files")
                    if len(files) > 10:
                        ctx.report_progress(100, 100)
                return files
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                logging.error(f"{error_msg} - list_files({path}, {depth})")

                if ctx:
                    ctx.error(error_msg)
                return [error_msg]

        @self.mcp.tool()
        def read_file(path: str, ctx: Context = None):
            """
            Read file content.

            Args:
                path: Path to the file
                ctx: MCP context object

            Return:
                File content as string
            """
            logging.info(f"Tool call: read_file(path={path})")
            if ctx:
                ctx.info(f"Reading file content from {path}")

            try:
                content = self.file_manager.read_file(path)
                logging.info(f"Successfully read file: {path} ({len(content)} bytes)")
                if ctx:
                    ctx.info(f"Successfully read file ({len(content)} bytes)")
                return content
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                logging.error(f"{error_msg} - read_file({path})")

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": str(e)}

        @self.mcp.tool()
        def get_file_info(path: str, ctx: Context = None) -> dict:
            """Get file information.

            Args:
                path: Path to the file
                ctx: MCP context object

            Return:
                Dictionary with file information
            """
            logging.info(f"Tool call: get_file_info(path={path})")
            if ctx:
                ctx.info(f"Getting file info for {path}")

            try:
                info = self.file_manager.get_file_info(path)
                logging.info(f"Retrieved file info for {path}")
                if ctx:
                    ctx.info(f"Retrieved file information successfully")
                return info
            except Exception as e:
                error_msg = str(e)
                logging.error(f"Error: {error_msg} - get_file_info({path})")

                if ctx:
                    ctx.error(f"Error getting file info: {error_msg}")

                return {"success": False, "error": error_msg}

        @self.mcp.tool()
        def get_file_mimetype(path: str, ctx: Context = None) -> str:
            """
            Get file MIME type.

            Args:
                path: Path to the file
                ctx: MCP context object

            Return:
                MIME type of the file
            """
            logging.info(f"Tool call: get_file_mimetype(path={path})")
            if ctx:
                ctx.info(f"Getting MIME type for {path}")

            try:
                mime_type = self.file_manager.get_file_mimetype(path)
                logging.info(f"Retrieved MIME type for {path}: {mime_type}")
                if ctx:
                    ctx.info(f"MIME type: {mime_type}")
                return mime_type
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                logging.error(f"{error_msg} - get_file_mimetype({path})")

                if ctx:
                    ctx.error(error_msg)

                return {"success": False, "error": error_msg}

        @self.mcp.tool()
        def search_files_by_name(
            pattern: str, path: Optional[str] = None, ctx: Context = None
        ) -> list:
            """
            Search files by name pattern.

            Args:
                pattern: Filename pattern to search for
                path: Path to search in (defaults to all root folders)
                ctx: MCP context object
            Return:
                List of matching file paths
            """
            logging.info(
                f"Tool call: search_files_by_name(pattern={pattern}, path={path})"
            )
            if ctx:
                ctx.info(
                    f"Searching for files matching '{pattern}' in {path or 'all root folders'}"
                )

            try:
                files = self.file_manager.search_files_by_name(pattern, path)
                logging.info(f"Found {len(files)} files matching '{pattern}'")
                if ctx:
                    ctx.info(f"Found {len(files)} matching files")
                    ctx.report_progress(100, 100)
                return files
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                logging.error(f"{error_msg} - search_files_by_name({pattern}, {path})")

                if ctx:
                    ctx.error(error_msg)

                return [error_msg]

        @self.mcp.tool()
        def search_files_by_content(
            query: str,
            path: Optional[str] = None,
            is_regex: bool = False,
            depth: int = 3,
            ctx: Context = None,
        ) -> list:
            """
            Search files by content.

            Args:
                query: Content to search for
                path: Path to search in (defaults to all root folders)
                is_regex: Whether to use regex search
                depth: Maximum directory depth to search (default: 3)
                ctx: MCP context object

            Return:
                List of matching file paths
            """
            logging.info(
                f"Tool call: search_files_by_content(query={query}, path={path}, is_regex={is_regex}, depth={depth})"
            )

            if ctx:
                ctx.info(
                    f"Searching for content '{query}' in {path or 'all root folders'} "
                    f"with max depth {depth} (using {'regex' if is_regex else 'plain text'} search)"
                )
                ctx.info("This operation might take some time for large directories")
                ctx.report_progress(5, 100)

            try:

                def progress_callback(current, total):
                    if ctx:
                        ctx.report_progress(current, total)
                        if current % 10 == 0 and current > 0:
                            ctx.info(f"Search progress: {current}%")

                files = self.file_manager.search_files_by_content(
                    query,
                    path,
                    is_regex,
                    max_depth=depth,
                    progress_callback=progress_callback,
                )

                if ctx:
                    ctx.report_progress(100, 100)

                logging.info(f"Found {len(files)} files containing '{query}'")
                if ctx:
                    ctx.info(f"Found {len(files)} files containing the search term")

                return files
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                logging.error(
                    f"{error_msg} - search_files_by_content({query}, {path}, {is_regex}, {depth})"
                )

                if ctx:
                    ctx.error(error_msg)

                return [error_msg]

    def run(self):
        """Run the MCP server."""
        try:
            logging.info("Starting FileMCP server")
            self.mcp.run(transport="stdio")
        except Exception as e:
            logging.error(f"Fatal error occurred: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="File MCP Server")
    parser.add_argument("--roots", nargs="*", help="Root folder paths")
    args = parser.parse_args()
    root_folders = (
        args.roots
        or os.environ.get("MCP_ROOT_FOLDERS", "").split(";")
        or [os.path.expanduser("~")]
    )

    root_folders = [path for path in root_folders if path]

    invalid_paths = []
    valid_paths = []

    for path in root_folders:
        if os.path.exists(path) and os.path.isdir(path):
            valid_paths.append(path)
        else:
            invalid_paths.append(path)

    if invalid_paths:
        logging.warning(
            f"The following root paths do not exist or are not directories: {invalid_paths}"
        )
        print(
            f"WARNING: The following root paths do not exist or are not directories: {invalid_paths}",
            file=sys.stderr,
        )

        if not valid_paths:
            logging.error("No valid root folders specified. Exiting.")
            print("ERROR: No valid root folders specified. Exiting.", file=sys.stderr)
            sys.exit(1)

    logging.info(f"Using root folders: {valid_paths}")

    mcp_server = FileMCP(root_folders=valid_paths)
    mcp_server.run()


if __name__ == "__main__":
    try:
        logging.info("Initializing File MCP server")
        main()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal. Gracefully shutting down...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error occurred during initialization: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
