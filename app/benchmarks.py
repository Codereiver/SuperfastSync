"""Benchmarking and metrics tracking module."""

import json
import socket
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class BenchmarkTracker:
    """Track upload/download performance metrics."""

    def __init__(self, data_file: str = "benchmarks.json"):
        self.data_file = Path(data_file)
        self._ensure_data_file()

    def _ensure_data_file(self) -> None:
        """Create benchmarks file if it doesn't exist."""
        if not self.data_file.exists():
            self.data_file.write_text("[]")

    def _load_data(self) -> list:
        """Load benchmark data from file."""
        try:
            return json.loads(self.data_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_data(self, data: list) -> None:
        """Save benchmark data to file."""
        self.data_file.write_text(json.dumps(data, indent=2))

    def reverse_dns_lookup(self, ip: str) -> Optional[str]:
        """
        Perform reverse DNS lookup for an IP address with timeout.

        Args:
            ip: IP address to lookup

        Returns:
            Hostname if found, None otherwise
        """
        try:
            # Set socket timeout to prevent hanging on slow/malicious DNS servers
            socket.setdefaulttimeout(2.0)
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except (socket.herror, socket.gaierror, socket.timeout):
            return None
        finally:
            # Reset socket timeout to default
            socket.setdefaulttimeout(None)

    def as_lookup(self, ip: str) -> Optional[str]:
        """
        Perform AS (Autonomous System) lookup.

        Note: This is a placeholder. For production, consider using:
        - ipwhois library
        - External API like ipinfo.io or ipapi.co
        - Local MaxMind GeoIP database
        """
        # Placeholder - in production you'd use an actual AS lookup service
        # For now, we'll just return None
        # TODO: Implement actual AS lookup if needed
        return None

    def record_transfer(
        self,
        operation: str,
        filename: str,
        file_size: int,
        duration: float,
        client_ip: str,
    ) -> dict:
        """
        Record a file transfer (upload or download).

        Args:
            operation: "upload" or "download"
            filename: Name of the file
            file_size: Size in bytes
            duration: Transfer duration in seconds
            client_ip: Client IP address

        Returns:
            The recorded benchmark entry
        """
        # Calculate speeds (bytes per second)
        avg_speed = file_size / duration if duration > 0 else 0

        # Perform lookups
        reverse_dns = self.reverse_dns_lookup(client_ip)
        asn = self.as_lookup(client_ip)

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operation": operation,
            "filename": filename,
            "file_size_bytes": file_size,
            "duration_seconds": round(duration, 3),
            "avg_speed_bps": int(avg_speed),
            "avg_speed_mbps": round(avg_speed * 8 / 1_000_000, 2),
            "client_ip": client_ip,
            "reverse_dns": reverse_dns,
            "asn": asn,
        }

        # Load, append, save
        data = self._load_data()
        data.append(entry)
        self._save_data(data)

        return entry

    def get_all_benchmarks(self) -> list:
        """Get all recorded benchmarks."""
        return self._load_data()

    def get_recent_benchmarks(self, limit: int = 50) -> list:
        """Get the most recent benchmarks."""
        data = self._load_data()
        return data[-limit:] if len(data) > limit else data


class TransferTimer:
    """Context manager for timing file transfers."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return False
