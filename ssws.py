import requests
import socket
import time
from termcolor import colored
import sys
import argparse
from requests.exceptions import RequestException
from collections import defaultdict

# Mimic browser headers to reduce discrepancies
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def normalize_fqdns(fqdns):
    normalized = set()
    for fqdn in fqdns:
        fqdn = fqdn.strip()
        if fqdn.startswith("www."):
            normalized.add(fqdn[4:])
        else:
            normalized.add(fqdn)
    
    sorted_fqdns = sorted(normalized)
    full_list = []
    for fqdn in sorted_fqdns:
        full_list.append(fqdn)
        full_list.append(f"www.{fqdn}")
    
    return sorted(set(full_list))

def resolve_ip(fqdn):
    try:
        return socket.gethostbyname(fqdn)
    except socket.gaierror:
        return "N/A"

def make_request(url):
    try:
        response = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=5)
        return response
    except RequestException:
        return None

def grab_banner_and_status(fqdn, port):
    try:
        url = f"http://{fqdn}:{port}/"
        if port == 443:
            url = f"https://{fqdn}:{port}/"
        response = requests.head(url, headers=HEADERS, allow_redirects=False, timeout=5)
        server = response.headers.get("Server", "Unknown")
        status_code = response.status_code
        return server, status_code
    except RequestException:
        return "No Response", None

def check_file(fqdn, port, path):
    url = f"http://{fqdn}:{port}{path}"
    if port == 443:
        url = f"https://{fqdn}:{port}{path}"
    response = make_request(url)
    if response:
        status_code = response.status_code
        if status_code == 200 and path == "/robots.txt":
            content = response.text.lower()
            if "user-agent:" in content or "disallow:" in content:
                return "robots.txt found!", status_code
        elif status_code == 200 and path == "/wp-login.php":
            content = response.text.lower()
            if (
                "username or email address" in content
                or "wp-includes" in content
                or "https://wordpress.org" in content
            ):
                return "WordPress detected!", status_code
        return f"No {path} found.", status_code
    return "No Response", None

def main():
    parser = argparse.ArgumentParser(
        description="Stupid Simple Web Scanner (ssws.py): Quickly scan FQDNs for WordPress, robots.txt, and more."
    )
    parser.add_argument("-i", "--input", required=True, help="Input file containing FQDNs, one per line.")
    parser.add_argument("--wp", "--wordpress", action="store_true", help="Check for WordPress login page (/wp-login.php).")
    parser.add_argument("--robots", action="store_true", help="Check for the presence of a robots.txt file.")
    parser.add_argument("-p", "--ports", default="80,443", help="Comma-separated list of ports to scan (default: 80,443).")
    
    args = parser.parse_args()
    
    with open(args.input, "r") as file:
        fqdns = [line.strip() for line in file if line.strip()]
    
    normalized_fqdns = normalize_fqdns(fqdns)
    ports = [int(p.strip()) for p in args.ports.split(",")]

    fqdn_to_ip = {fqdn: resolve_ip(fqdn) for fqdn in normalized_fqdns}

    # Print header row
    print(f"{'FQDN':<30} {'IP':<15} {'Port':<5} {'Code':<6} {'Result':<40} {'Server':<20}")

    for fqdn, ip in fqdn_to_ip.items():
        for port in ports:
            banner, status_code = grab_banner_and_status(fqdn, port)
            if not status_code:
                continue

            # Highlight redirects (3xx) in orange
            status_str = (
                colored(str(status_code), "yellow") if 300 <= status_code < 400 else str(status_code)
            )

            result_line = f"{fqdn:<30} {ip:<15} {port:<5} {status_str:<6}"

            if args.wp:
                wp_result, wp_code = check_file(fqdn, port, "/wp-login.php")
                result_line += f"{wp_result:<40}"

            if args.robots:
                robots_result, robots_code = check_file(fqdn, port, "/robots.txt")
                result_line += f"{robots_result:<40}"

            result_line += f"{banner:<20}"
            print(result_line)

if __name__ == "__main__":
    main()
