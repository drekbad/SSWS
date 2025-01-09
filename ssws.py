import requests
import socket
import time
from termcolor import colored
import sys
import argparse
from requests.exceptions import RequestException
from collections import defaultdict

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
        return None

def detect_dynamic_dns(fqdn):
    try:
        ips = set()
        for _ in range(3):  # Resolve the IP 3 times with a small delay
            ips.add(socket.gethostbyname(fqdn))
            time.sleep(1)
        return len(ips) > 1
    except socket.gaierror:
        return False

def check_redirect(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.url != url:
            return response.status_code, response.url
    except RequestException:
        pass
    return None, None

def grab_banner(fqdn, port):
    try:
        url = f"http://{fqdn}:{port}/"
        if port == 443:
            url = f"https://{fqdn}:{port}/"
        response = requests.head(url, timeout=5)
        return response.headers.get("Server", "Unknown"), response.status_code
    except RequestException:
        return "No Response", None

def check_wordpress(fqdn, port):
    url = f"http://{fqdn}:{port}/wp-login.php"
    if port == 443:
        url = f"https://{fqdn}:{port}/wp-login.php"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            content = response.text.lower()
            if (
                "username or email address" in content
                or "wp-includes" in content
                or "https://wordpress.org" in content
            ):
                return colored("WordPress detected!", "green"), response.status_code
        return colored("No WordPress instance found.", "red"), response.status_code
    except RequestException:
        return "No Response", None

def check_robots(fqdn, port):
    url = f"http://{fqdn}:{port}/robots.txt"
    if port == 443:
        url = f"https://{fqdn}:{port}/robots.txt"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            content = response.text.lower()
            if "user-agent:" in content or "disallow:" in content:
                return colored("robots.txt found!", "green"), response.status_code
        return colored("No robots.txt found.", "red"), response.status_code
    except RequestException:
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

    if not args.wp and not args.robots:
        print("Error: You must specify at least one check option (--wp or --robots).")
        sys.exit(1)

    fqdn_to_ip = {fqdn: resolve_ip(fqdn) for fqdn in normalized_fqdns}
    grouped_fqdns = defaultdict(list)

    for fqdn, ip in fqdn_to_ip.items():
        grouped_fqdns[ip].append(fqdn)

    results = []
    for ip, fqdns in grouped_fqdns.items():
        for fqdn in fqdns:
            for port in ports:
                banner, status_code = grab_banner(fqdn, port)
                if not status_code:  # Skip if no response
                    continue

                dynamic_dns = "Yes" if detect_dynamic_dns(fqdn) else "No"
                result_line = f"{fqdn:<30} {port:<5} {status_code:<5} "
                
                # Highlight redirects in blue
                if 300 <= status_code < 400:
                    result_line += colored(str(status_code), "blue") + " "
                
                if args.wp:
                    wp_result, wp_code = check_wordpress(fqdn, port)
                    result_line += f"{wp_result:<40} "

                if args.robots:
                    robots_result, robots_code = check_robots(fqdn, port)
                    result_line += f"{robots_result:<40} "

                result_line += f"{banner:<20} Dynamic DNS: {dynamic_dns}"
                results.append(result_line)

        # Add a line break between groups of FQDNs sharing the same IP
        results.append("")

    print("\n".join(results))

if __name__ == "__main__":
    main()
