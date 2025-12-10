"""AvocadoDB Auto-Management for DeepAgents CLI.

Automatically handles:
- Installing AvocadoDB binary
- Starting/stopping server as subprocess
- Auto-ingesting current directory
- File watching for updates (optional)
"""

import atexit
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

import requests


class AvocadoDBManager:
    """Manages AvocadoDB server lifecycle automatically."""

    def __init__(self, auto_start: bool = True, auto_ingest: bool = True, background_ingest: bool = True):
        """Initialize AvocadoDB manager.

        Args:
            auto_start: Automatically start server if not running
            auto_ingest: Automatically ingest current directory on first start
            background_ingest: Periodically re-ingest changed files in background
        """
        self.server_url = os.environ.get("AVOCADODB_URL", "http://localhost:8765")
        self.auto_start = auto_start
        self.auto_ingest = auto_ingest
        self.background_ingest = background_ingest
        self.server_process: Optional[subprocess.Popen] = None
        self.binary_path: Optional[Path] = None
        self._ingest_thread: Optional[threading.Thread] = None
        self._stop_ingest = threading.Event()
        self._last_ingested: dict[Path, float] = {}  # Track file modification times

        # Find or install AvocadoDB
        if self.auto_start:
            self._ensure_available()

    def _find_binary(self) -> Optional[Path]:
        """Find AvocadoDB binary in common locations."""
        possible_paths = [
            # In current directory
            Path.cwd() / "target/release/avocado-server",
            # In parent directories (up to 3 levels)
            Path.cwd().parent / "target/release/avocado-server",
            Path.cwd().parent.parent / "target/release/avocado-server",
            Path.cwd().parent.parent.parent / "target/release/avocado-server",
            # In home directory
            Path.home() / ".avocadodb/avocado-server",
            # System-wide
            Path("/usr/local/bin/avocado-server"),
        ]

        for path in possible_paths:
            if path.exists() and path.is_file():
                return path

        return None

    def _install_binary(self) -> Optional[Path]:
        """Install AvocadoDB binary automatically.

        Downloads pre-built binary or builds from source.
        """
        install_dir = Path.home() / ".avocadodb"
        install_dir.mkdir(exist_ok=True)

        print("🥑 Installing AvocadoDB...")
        print("   This only happens once, please wait...")

        try:
            # Try to download pre-built binary (if available)
            # For now, clone and build from source
            repo_dir = install_dir / "repo"

            if not repo_dir.exists():
                print("   Cloning repository...")
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "https://github.com/servesys-labs/avacadodb.git",
                        str(repo_dir),
                    ],
                    check=True,
                    capture_output=True,
                )

            print("   Building (this may take 2-3 minutes)...")
            subprocess.run(
                ["cargo", "build", "--release"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )

            # Copy binary to install location
            binary_src = repo_dir / "target/release/avocado-server"
            binary_dst = install_dir / "avocado-server"

            if binary_src.exists():
                import shutil

                shutil.copy2(binary_src, binary_dst)
                binary_dst.chmod(0o755)
                print(f"✅ Installed to {binary_dst}")
                return binary_dst

        except Exception as e:
            print(f"⚠️  Auto-install failed: {e}")
            print("   Please install manually:")
            print("   git clone https://github.com/servesys-labs/avacadodb")
            print("   cd avacadodb && cargo build --release")

        return None

    def _ensure_available(self):
        """Ensure AvocadoDB binary is available."""
        self.binary_path = self._find_binary()

        if not self.binary_path and self.auto_start:
            # Try to install automatically
            self.binary_path = self._install_binary()

    def is_running(self) -> bool:
        """Check if AvocadoDB server is running."""
        try:
            response = requests.get(f"{self.server_url}/stats", timeout=1)
            return response.status_code == 200
        except:
            return False

    def start_server(self) -> bool:
        """Start AvocadoDB server as background subprocess.

        Returns:
            True if server started successfully
        """
        if self.is_running():
            # Server already running - no need to start
            return True

        if not self.binary_path:
            print("⚠️  AvocadoDB binary not found")
            return False

        print("🥑 Starting AvocadoDB server...")

        try:
            # Extract port from server_url for PORT env var
            import urllib.parse
            parsed_url = urllib.parse.urlparse(self.server_url)
            port = str(parsed_url.port or 8080)

            # Start server in background with PORT env var
            env = os.environ.copy()
            env["PORT"] = port

            self.server_process = subprocess.Popen(
                [str(self.binary_path)],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,  # Detach from parent
            )

            # Wait for server to be ready
            for _ in range(10):
                time.sleep(0.5)
                if self.is_running():
                    print("✅ Server started (daemon mode - stays running)")

                    # DO NOT register cleanup on exit - let server run as daemon
                    # User can manually stop with: pkill avocado-server
                    # atexit.register(self.stop_server)  # DISABLED for persistence

                    # Auto-ingest current directory
                    if self.auto_ingest:
                        self._auto_ingest()

                    return True

            print("⚠️  Server failed to start")
            return False

        except Exception as e:
            print(f"⚠️  Failed to start server: {e}")
            return False

    def stop_server(self):
        """Stop AvocadoDB server subprocess."""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("🥑 AvocadoDB server stopped")
            except:
                self.server_process.kill()

    def _detect_project_type(self, cwd: Path) -> list[str]:
        """Detect project type and return appropriate source patterns."""
        patterns = []

        # Python project
        if (cwd / "pyproject.toml").exists() or (cwd / "setup.py").exists() or (cwd / "requirements.txt").exists():
            patterns.extend(["**/*.py", "**/*.pyi"])

        # JavaScript/TypeScript (Node.js)
        if (cwd / "package.json").exists():
            patterns.extend(["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"])

        # Rust
        if (cwd / "Cargo.toml").exists():
            patterns.extend(["**/*.rs"])

        # Go
        if (cwd / "go.mod").exists():
            patterns.extend(["**/*.go"])

        # Java/Kotlin
        if (cwd / "pom.xml").exists() or (cwd / "build.gradle").exists():
            patterns.extend(["**/*.java", "**/*.kt"])

        # C/C++
        if (cwd / "Makefile").exists() or (cwd / "CMakeLists.txt").exists():
            patterns.extend(["**/*.c", "**/*.cpp", "**/*.h", "**/*.hpp"])

        # Ruby
        if (cwd / "Gemfile").exists():
            patterns.extend(["**/*.rb"])

        # PHP
        if (cwd / "composer.json").exists():
            patterns.extend(["**/*.php"])

        # If no project type detected, use common patterns
        if not patterns:
            patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.java", "**/*.go", "**/*.rs"]

        return patterns

    def _auto_ingest(self):
        """Auto-ingest current directory on first start."""
        if not self.binary_path:
            return

        cwd = Path.cwd()
        print(f"🥑 Auto-ingesting {cwd}...")

        # Find ingest binary
        ingest_binary = self.binary_path.parent / "avocado"

        if not ingest_binary.exists():
            print("   Skipping auto-ingest (binary not found)")
            return

        try:
            # Detect project type and get appropriate patterns
            source_patterns = self._detect_project_type(cwd)

            # Always ingest documentation
            doc_patterns = [
                "README.md",
                "QUICKSTART.md",
                "docs/**/*.md",
                "*.md",
            ]

            # Combine all patterns
            all_patterns = doc_patterns + source_patterns

            paths_to_ingest = []
            for pattern in all_patterns:
                try:
                    matching = list(cwd.glob(pattern))
                    # Exclude common directories
                    matching = [
                        p for p in matching
                        if not any(part in p.parts for part in [
                            "node_modules", ".git", "venv", ".venv",
                            "__pycache__", "target", "build", "dist",
                            ".next", ".cache"
                        ])
                    ]
                    paths_to_ingest.extend(matching[:50])  # Limit per pattern
                except:
                    pass

            if not paths_to_ingest:
                print("   No documentation found to ingest")
                return

            # Ingest each path (limit to 100 files total)
            for path in paths_to_ingest[:100]:
                subprocess.run(
                    [str(ingest_binary), "ingest", str(path)],
                    capture_output=True,
                    timeout=30,
                )

            print(f"✅ Auto-ingested {len(paths_to_ingest)} items")

        except Exception as e:
            print(f"   Auto-ingest error: {e}")

    def _background_ingest_loop(self):
        """Background thread that periodically re-ingests changed files."""
        cwd = Path.cwd()

        while not self._stop_ingest.is_set():
            try:
                # Check for changed files every 30 seconds
                if self._stop_ingest.wait(timeout=30):
                    break

                if not self.is_running() or not self.binary_path:
                    continue

                ingest_binary = self.binary_path.parent / "avocado"
                if not ingest_binary.exists():
                    continue

                # Find files matching our patterns
                paths_to_check = []
                for pattern in ["docs/**/*.md", "README.md", "*.md", "src/**/*.py", "src/**/*.ts", "src/**/*.js"]:
                    try:
                        matching = list(cwd.glob(pattern))
                        paths_to_check.extend(matching[:50])  # Limit to prevent too many files
                    except:
                        pass

                # Re-ingest files that have changed
                re_ingested = 0
                for path in paths_to_check:
                    if not path.is_file():
                        continue

                    try:
                        mtime = path.stat().st_mtime
                        last_mtime = self._last_ingested.get(path, 0)

                        # If file is new or modified, re-ingest
                        if mtime > last_mtime:
                            subprocess.run(
                                [str(ingest_binary), "ingest", str(path)],
                                capture_output=True,
                                timeout=10,
                            )
                            self._last_ingested[path] = mtime
                            re_ingested += 1
                    except:
                        pass

                if re_ingested > 0:
                    print(f"🥑 Background: Re-ingested {re_ingested} changed files")

            except Exception:
                pass  # Silently continue on errors

    def _start_background_ingest(self):
        """Start background ingestion thread."""
        if self.background_ingest and not self._ingest_thread:
            self._ingest_thread = threading.Thread(
                target=self._background_ingest_loop,
                daemon=True,
                name="AvocadoDB-Ingest"
            )
            self._ingest_thread.start()

    def _stop_background_ingest(self):
        """Stop background ingestion thread."""
        if self._ingest_thread:
            self._stop_ingest.set()
            self._ingest_thread.join(timeout=2)
            self._ingest_thread = None


# Global instance
_manager: Optional[AvocadoDBManager] = None


def get_manager() -> AvocadoDBManager:
    """Get or create global AvocadoDB manager instance."""
    global _manager
    if _manager is None:
        # Auto-start ENABLED by default (can disable with AVOCADODB_AUTO_START=false)
        auto_start = os.environ.get("AVOCADODB_AUTO_START", "true").lower() == "true"
        _manager = AvocadoDBManager(auto_start=auto_start, auto_ingest=auto_start)

    return _manager


def ensure_running() -> bool:
    """Ensure AvocadoDB server is running.

    Returns:
        True if server is available
    """
    manager = get_manager()

    if manager.is_running():
        return True

    if manager.auto_start:
        return manager.start_server()

    return False


def get_stats() -> dict:
    """Get indexing statistics from AvocadoDB server.

    Returns:
        Dict with stats like item_count, index_size, etc.
        Returns empty dict if server is not available.
    """
    manager = get_manager()

    if not manager.is_running():
        return {}

    try:
        response = requests.get(f"{manager.server_url}/stats", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass

    return {}


def get_startup_info() -> str:
    """Get startup information for AvocadoDB.

    Returns:
        Formatted string with server status and indexing stats.
    """
    manager = get_manager()

    # Ensure server is running (will auto-start if needed)
    is_running = ensure_running()

    if not is_running:
        return "  [dim]🥑 AvocadoDB: Not available (install with: pip install avocadodb)[/dim]"

    # Get stats
    stats = get_stats()

    if not stats:
        return "  [dim]🥑 AvocadoDB: Server running (no stats available)[/dim]"

    # Extract useful stats
    artifacts_count = stats.get("artifacts_count", 0)
    spans_count = stats.get("spans_count", 0)
    total_tokens = stats.get("total_tokens", 0)

    # Format the message
    if artifacts_count > 0:
        return f"  [green]🥑 AvocadoDB: Ready[/green] [dim]({artifacts_count} docs, {spans_count} spans, {total_tokens:,} tokens)[/dim]"
    else:
        return "  [yellow]🥑 AvocadoDB: Ready[/yellow] [dim](no items indexed yet - will auto-ingest on first query)[/dim]"


__all__ = ["AvocadoDBManager", "get_manager", "ensure_running", "get_stats", "get_startup_info"]
