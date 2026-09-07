import io
import socket
import sys
import argparse
import qrcode

def get_local_ip() -> str:
    """Attempts to discover the machine's primary local network IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def generate_qr_code_str(url: str) -> str:
    """Generates a QR code string representation compatible with all terminal stdout encodings."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Try block characters first, fall back to '##' if stdout codec (e.g. cp1252) can't encode unicode
    block_lines = ["".join("██" if cell else "  " for cell in row) for row in qr.modules]
    block_text = "\n".join(block_lines)
    
    stdout_encoding = getattr(sys.stdout, 'encoding', None) or 'ascii'
    try:
        block_text.encode(stdout_encoding)
        return block_text
    except (UnicodeEncodeError, TypeError):
        ascii_lines = ["".join("##" if cell else "  " for cell in row) for row in qr.modules]
        return "\n".join(ascii_lines)


def print_startup_banner(ip: str, port: int) -> str:
    """Prints a styled terminal banner with server URL and scannable QR code."""
    url = f"http://{ip}:{port}"
    qr_art = generate_qr_code_str(url)
    
    banner = f"""
===================================================================
             Sanctuary Mobile Mode - Local Server                  
===================================================================


 Connect your mobile device on the same Wi-Fi network:
 
 URL:  {url}

 Scan QR Code below with your mobile camera:

{qr_art}
 Note: If your mobile device cannot connect, ensure port {port} is allowed
 through Windows Defender Firewall.
===================================================================
"""
    print(banner)
    return banner

def main():
    parser = argparse.ArgumentParser(description="Hymnody Manager LAN Server Launcher")
    parser.add_argument("--host", default=None, help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    args = parser.parse_args()

    local_ip = get_local_ip()
    host = args.host if args.host else "0.0.0.0"
    
    display_ip = local_ip if host == "0.0.0.0" else host
    print_startup_banner(display_ip, args.port)

    import uvicorn
    uvicorn.run("src.main:app", host=host, port=args.port, reload=not args.no_reload)

if __name__ == "__main__":
    main()
