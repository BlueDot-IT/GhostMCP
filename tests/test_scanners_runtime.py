import ssl
import unittest
from unittest.mock import MagicMock, patch

from ghostmcp.scanners import (
    ScannerError,
    ScannerTimeoutError,
    run_external_binary,
    tls_certificate,
)


class ScannerRuntimeTests(unittest.TestCase):
    @patch("ghostmcp.scanners.socket.create_connection")
    @patch("ghostmcp.scanners.ssl.create_default_context")
    def test_tls_certificate_requires_tls_1_2_or_newer(
        self, mock_create_context, mock_create_connection
    ) -> None:
        context = MagicMock()
        tls_socket = MagicMock()
        tls_socket.__enter__.return_value.getpeercert.return_value = {
            "notBefore": "Jan 01 00:00:00 2026 GMT",
            "notAfter": "Jan 01 00:00:00 2027 GMT",
        }
        context.wrap_socket.return_value = tls_socket
        mock_create_context.return_value = context

        tcp_socket = MagicMock()
        tcp_socket.__enter__.return_value = tcp_socket
        mock_create_connection.return_value = tcp_socket

        tls_certificate("internal.example")

        self.assertEqual(context.minimum_version, ssl.TLSVersion.TLSv1_2)
        context.wrap_socket.assert_called_once_with(
            tcp_socket, server_hostname="internal.example"
        )

    def test_command_redaction_hides_sensitive_values(self) -> None:
        from ghostmcp.scanners import _redact_command

        command = [
            "sqlmap",
            "--auth-cred=user:secret",
            "--token",
            "token-value",
        ]
        self.assertEqual(
            _redact_command(command),
            [
                "sqlmap",
                "--auth-cred=<redacted>",
                "--token",
                "<redacted>",
            ],
        )

    def test_smbmap_password_is_redacted(self) -> None:
        from ghostmcp.scanners import _redact_command

        self.assertEqual(
            _redact_command(
                ["smbmap", "-H", "10.0.0.2", "-u", "u", "-p", "secret"]
            ),
            [
                "smbmap",
                "-H",
                "10.0.0.2",
                "-u",
                "u",
                "-p",
                "<redacted>",
            ],
        )

    def test_missing_binary(self) -> None:
        with self.assertRaises(ScannerError):
            run_external_binary("__ghostmcp_missing_binary__")

    def test_timeout_enforced(self) -> None:
        with self.assertRaises(ScannerTimeoutError):
            run_external_binary("sh", ["-c", "sleep 2"], timeout_s=0.1)

    def test_output_truncation(self) -> None:
        result = run_external_binary(
            "sh",
            ["-c", "for i in $(seq 1 2000); do echo X; done"],
            timeout_s=5,
            max_stdout_bytes=128,
            max_stderr_bytes=64,
        )
        self.assertIn("output_truncated", result)
        self.assertLessEqual(len(result["stdout"].encode("utf-8")), 128)


if __name__ == "__main__":
    unittest.main()
