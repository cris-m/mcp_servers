import fnmatch
import mimetypes
import os
import re


class FileManager:
    DEFAULT_IGNORE_PATTERNS = {
        "version_control": [".git*", ".hg", ".svn", ".bzr"],
        "operating_system": [".DS_Store", "Thumbs.db", "desktop.ini", "$RECYCLE.BIN"],
        "ide_editor": [".vscode", ".idea", "*.sublime-*", "*.code-workspace"],
        "python": [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".coverage",
            "*.pyc",
            "*.pyo",
            "*.pyd",
        ],
        "dependencies": ["node_modules", "bower_components", "vendor"],
        "logs_temp": ["*.log", "*.tmp", "*.swp", "*.bak", "*.cache"],
        "security": ["*.crt", "*.key", "*.pem", "*.pfx", "*.p12"],
        "config": ["*.cfg", "*.conf", "*.ini", "*.env"],
        "database": ["*.sqlite*", "*.db*", "*.mdb"],
        "archives": ["*.tar", "*.gz", "*.zip", "*.rar", "*.7z", "*.bz2"],
        "development": ["*.min.*", "*.map"],
    }

    DEFAULT_RESTRICTED_PATHS = [
        "/etc",
        "/var",
        "/root",
        "/sys",
        "/proc",
        "/boot",
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\Users\\*\\AppData",
        "/usr/bin",
        "/bin",
        "/sbin",
        "/system",
    ]

    def __init__(
        self,
        root_folders,
        restricted_folders=None,
        restricted_files=None,
        ignore_patterns=None,
        include_defaults=True,
    ):
        self.root_folders = self._initialize_root_folders(root_folders)

        self.restricted_folders, self.restricted_files = self._initialize_restrictions(
            restricted_folders, restricted_files, ignore_patterns, include_defaults
        )

    def _initialize_root_folders(self, root_folders):
        if isinstance(root_folders, str):
            root_folders = [root_folders]

        normalized_folders = []
        for folder in root_folders:
            abs_folder = os.path.abspath(os.path.normpath(folder))

            if not os.path.isdir(abs_folder):
                raise ValueError(f"Root folder {abs_folder} does not exist.")

            normalized_folders.append(abs_folder)

        return normalized_folders

    def _initialize_restrictions(
        self,
        restricted_folders=None,
        restricted_files=None,
        ignore_patterns=None,
        include_defaults=True,
    ):
        folder_restrictions = []
        file_restrictions = []

        if include_defaults:
            folder_restrictions, file_restrictions = self._add_default_restrictions()

        if ignore_patterns:
            for _, patterns in ignore_patterns.items():
                folder_patterns, file_patterns = self._categorize_patterns(patterns)
                folder_restrictions.extend(folder_patterns)
                file_restrictions.extend(file_patterns)

        if restricted_folders:
            folder_restrictions.extend(restricted_folders)

        if restricted_files:
            file_restrictions.extend(restricted_files)

        absolute_paths = [p for p in folder_restrictions if os.path.isabs(p)]
        relative_paths = [p for p in folder_restrictions if not os.path.isabs(p)]

        absolute_paths = self._normalize_folder_paths(absolute_paths)

        folder_restrictions = absolute_paths + relative_paths

        return folder_restrictions, file_restrictions

    def _add_default_restrictions(self):
        folder_restrictions = list(self.DEFAULT_RESTRICTED_PATHS)
        file_restrictions = []

        for _, patterns in self.DEFAULT_IGNORE_PATTERNS.items():
            folder_patterns, file_patterns = self._categorize_patterns(patterns)
            folder_restrictions.extend(folder_patterns)
            file_restrictions.extend(file_patterns)

        return folder_restrictions, file_restrictions

    def _categorize_patterns(self, patterns):
        folder_patterns = []
        file_patterns = []

        for pattern in patterns:
            if pattern.endswith("/") or "." not in os.path.basename(pattern):
                folder_patterns.append(pattern)
            else:
                file_patterns.append(pattern)

        return folder_patterns, file_patterns

    def _normalize_folder_paths(self, folder_paths):
        normalized_paths = []

        for path in folder_paths:
            if os.path.isabs(path):
                normalized_paths.append(os.path.abspath(os.path.normpath(path)))
            else:
                normalized_paths.append(path)

        return normalized_paths

    def _content_matches(self, content, query, is_regex):
        if is_regex:
            try:
                pattern = re.compile(query, re.IGNORECASE)
                return pattern.search(content) is not None
            except re.error:
                return False
        return query.lower() in content.lower()

    def _is_in_root_folders(self, path):
        for root in self.root_folders:
            if path.startswith(root):
                return True
        return False

    def _is_restricted_path(self, path):

        for restricted in self.restricted_folders:
            if os.path.isabs(restricted):
                if "*" in restricted:
                    regex_pattern = (
                        "^" + re.escape(restricted).replace("\\*", ".*") + ".*$"
                    )
                    if re.match(regex_pattern, path):
                        return True
                elif path.startswith(restricted):
                    return True
            else:

                path_parts = path.split(os.sep)
                restricted_parts = restricted.split(os.sep)

                for i in range(len(path_parts) - len(restricted_parts) + 1):
                    match = True
                    for j in range(len(restricted_parts)):
                        if not fnmatch.fnmatch(path_parts[i + j], restricted_parts[j]):
                            match = False
                            break
                    if match:
                        return True

        filename = os.path.basename(path)
        for pattern in self.restricted_files:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def _validate_path(self, path):
        abs_path = os.path.abspath(os.path.normpath(path))

        if not self._is_in_root_folders(abs_path):
            raise ValueError(f"Path {abs_path} is outside all root folders")

        if self._is_restricted_path(abs_path):
            raise ValueError(f"Path {abs_path} is in a restricted area")

        return abs_path

    def _is_likely_binary(self, path):
        """Check if a file is likely binary based on extension."""
        binary_extensions = {
            ".bin",
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".obj",
            ".o",
            ".pyc",
            ".pyd",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".ico",
            ".webp",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
            ".flv",
            ".wmv",
            ".wma",
            ".ogg",
            ".wav",
            ".zip",
            ".tar",
            ".gz",
            ".bz2",
            ".7z",
            ".rar",
            ".iso",
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".db",
            ".sqlite",
            ".mdb",
            ".accdb",
        }
        ext = os.path.splitext(path)[1].lower()
        return ext in binary_extensions

    def list_files(self, path=None, depth=1):
        result = []

        if path is None:

            paths = self.root_folders
        else:
            paths = [path]

        for current_path in paths:
            validated_path = self._validate_path(current_path)

            for root, dirs, files in os.walk(validated_path):
                dirs[:] = [
                    d
                    for d in dirs
                    if not self._is_restricted_path(os.path.join(root, d))
                ]

                current_depth = root[len(validated_path) :].count(os.sep)

                if current_depth >= depth:
                    del dirs[:]
                    continue

                for file in files:
                    full_path = os.path.join(root, file)
                    if not self._is_restricted_path(full_path):
                        result.append(full_path)

        return result

    def read_file(self, path):
        validated_path = self._validate_path(path)

        if not os.path.isfile(validated_path):
            raise ValueError(f"{validated_path} is not a file")

        with open(validated_path, "r", encoding="utf-8") as file:
            return file.read()

    def get_file_info(self, path):
        validated_path = self._validate_path(path)

        if not os.path.isfile(validated_path):
            raise ValueError(f"{validated_path} is not a file")

        stat = os.stat(validated_path)
        return {
            "path": validated_path,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
        }

    def get_file_mimetype(self, path):
        validated_path = self._validate_path(path)

        if not os.path.isfile(validated_path):
            raise ValueError(f"{validated_path} is not a file")

        mime_type, _ = mimetypes.guess_type(validated_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
        return mime_type

    def search_files_by_name(self, pattern, path=None, max_depth=5):
        if path is None:
            paths = self.root_folders
        else:
            paths = [path]

        result = []

        for search_path in paths:
            validated_path = self._validate_path(search_path)

            for root, dirs, files in os.walk(validated_path):
                current_depth = root[len(validated_path) :].count(os.sep)
                if current_depth >= max_depth:
                    dirs[:] = []
                    continue

                dirs[:] = [
                    d
                    for d in dirs
                    if not self._is_restricted_path(os.path.join(root, d))
                ]

                for file in files:
                    full_path = os.path.join(root, file)
                    if not self._is_restricted_path(full_path) and fnmatch.fnmatch(
                        file, pattern
                    ):
                        result.append(full_path)

        return result

    def search_files_by_content(
        self, query, path=None, is_regex=False, max_depth=3, progress_callback=None
    ):
        if path is None:
            paths = self.root_folders
        else:
            paths = [path]

        result = []
        encodings = (
            "utf-8-sig",
            "utf-8",
            "utf-16-le",
            "utf-16-be",
            "latin-1",
            "euc-jp",
            "iso-2022-jp",
        )

        dirs_processed = 0
        total_dirs = 100
        files_processed = 0

        if progress_callback:
            progress_callback(5, 100)

        for search_path in paths:
            validated_path = self._validate_path(search_path)

            for root, dirs, files in os.walk(validated_path):
                dirs_processed += 1

                current_depth = root[len(validated_path) :].count(os.sep)

                if current_depth >= max_depth:
                    dirs[:] = []
                    continue

                if progress_callback and dirs_processed % 5 == 0:
                    progress = min(int((dirs_processed / total_dirs) * 80) + 5, 85)
                    progress_callback(progress, 100)

                dirs[:] = [
                    d
                    for d in dirs
                    if not self._is_restricted_path(os.path.join(root, d))
                ]

                for file in files:
                    files_processed += 1
                    full_path = os.path.join(root, file)
                    if self._is_restricted_path(full_path):
                        continue

                    try:
                        if os.path.getsize(full_path) > 5 * 1024 * 1024:
                            continue
                    except OSError:
                        continue

                    if self._is_likely_binary(full_path):
                        continue

                    for encoding in encodings:
                        try:
                            with open(full_path, "r", encoding=encoding) as f:
                                content = f.read()
                                if self._content_matches(content, query, is_regex):
                                    result.append(full_path)
                                    break
                        except UnicodeDecodeError:
                            continue
                        except (IOError, PermissionError):
                            break

        if progress_callback:
            progress_callback(100, 100)

        return result
