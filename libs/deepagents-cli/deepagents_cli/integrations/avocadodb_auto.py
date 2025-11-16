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
import time
from pathlib import Path
from typing import Optional

import requests


class AvocadoDBManager:
    """Manages AvocadoDB server lifecycle automatically."""

    def __init__(self, auto_start: bool = True, auto_ingest: bool = True):
        """Initialize AvocadoDB manager.

        Args:
            auto_start: Automatically start server if not running
            auto_ingest: Automatically ingest current directory on first start
        """
        self.server_url = os.environ.get("AVOCADODB_URL", "http://localhost:8765")
        self.auto_start = auto_start
        self.auto_ingest = auto_ingest
        self.server_process: Optional[subprocess.Popen] = None
        self.binary_path: Optional[Path] = None

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
            print("🥑 AvocadoDB server already running")
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
                    print("✅ Server started")

                    # Register cleanup on exit
                    atexit.register(self.stop_server)

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
            # Ingest common documentation paths
            paths_to_ingest = []

            for pattern in ["docs", "README.md", "*.md", "src"]:
                matching = list(cwd.glob(pattern))
                paths_to_ingest.extend(matching)

            if not paths_to_ingest:
                print("   No documentation found to ingest")
                return

            # Ingest each path
            for path in paths_to_ingest[:10]:  # Limit to 10 paths
                subprocess.run(
                    [str(ingest_binary), "ingest", str(path)],
                    capture_output=True,
                    timeout=30,
                )

            print(f"✅ Auto-ingested {len(paths_to_ingest)} items")

        except Exception as e:
            print(f"   Auto-ingest error: {e}")


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


__all__ = ["AvocadoDBManager", "get_manager", "ensure_running"]
