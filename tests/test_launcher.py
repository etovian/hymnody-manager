import pytest
from unittest.mock import patch, MagicMock

import run_server

def test_get_local_ip_success():
    mock_socket = MagicMock()
    mock_socket.getsockname.return_value = ('192.168.1.100', 12345)
    
    with patch('socket.socket') as mock_sock_cls:
        mock_sock_cls.return_value.__enter__.return_value = mock_socket
        ip = run_server.get_local_ip()
        assert ip == '192.168.1.100'

def test_get_local_ip_fallback_on_error():
    with patch('socket.socket', side_effect=OSError("Network unreachable")):
        ip = run_server.get_local_ip()
        assert ip == '127.0.0.1'

def test_generate_qr_code_str():
    url = "http://192.168.1.100:8000"
    qr_str = run_server.generate_qr_code_str(url)
    assert isinstance(qr_str, str)
    assert len(qr_str) > 0

def test_print_startup_banner(capsys):
    run_server.print_startup_banner("192.168.1.100", 8000)
    captured = capsys.readouterr()
    assert "Sanctuary Mobile Mode - Local Server" in captured.out
    assert "http://192.168.1.100:8000" in captured.out
    assert "Windows Defender Firewall" in captured.out

