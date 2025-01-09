import requests
from termcolor import colored
import sys
import argparse
from requests.exceptions import RequestException

def normalize_fqdns(fqdns):
    """
    Normalize FQDNs by ensuring www. and non-www. versions are paired and sorted alphabetically.
    """
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
    
    return sorted(set(full_list))  # Remove duplicates if both versions were in the input.

def check_redirect(url):
    """
    Check if a URL processes a redirect and return the final URL or None if no redirect.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.url != url:
            return response.url
    except RequestException:
        pass
    return None

def grab_banner(fqdn, port):
    """
    Attempt to grab the banner from the web server.
    """
    try:
        url = f"http://{fqdn}:{port}/"
        if port == 443:
            url = f"https://{fqdn}:{port}/"
        response = requests.head(url, timeout=5)
        server = response.headers.get("Server", "Unknown")
        return server
    except RequestException:
        return "No Response"

def check_wordpress(fqdn, port):
    """
    Check if a given FQDN's /wp-login.php page is a WordPress login page.
    """
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
                return colored("WordPress detected!", "green")
        return colored("No WordPress instance found.", "red")
    except RequestException:
        return "No Response"

def check_robots(fqdn, port):
    """
    Check if a given FQDN has a robots.txt file and contains "User-agent:" or "Disallow:".
    """
    url = f"http://{fqdn}:{port}/robots.txt"
    if port == 443:
        url = f"https://{fqdn}:{port}/robots.txt"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            content = response.text.lower()
            if "user-agent:" in content or "disallow:" in content:
                return colored("robots.txt found!", "green")
        return colored("No robots.txt found.", "red")
    except RequestException:
        return "No Response"

def main():
    parser = argparse.ArgumentParser(
        description="Stupid Simple Web Scanner (ssws.py): Quickly scan FQDNs for WordPress or robots.txt presence."
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Input file containing FQDNs, one per line."
    )
    parser.add_argument(
        "--wp", "--wordpress", action="store_true", help="Check for WordPress login page (/wp-login.php)."
    )
    parser.add_argument(
        "--robots", action="store_true", help="Check for the presence of a robots.txt file."
    )
    parser.add_argument(
        "-p", "--ports", default="80,443", help="Comma-separated list of ports to scan (default: 80,443)."
    )
    
    args = parser.parse_args()

    # Read the input file containing FQDNs
    with open(args.input, "r") as file:
        fqdns = [line.strip() for line in file if line.strip()]

    # Normalize and prepare FQDN list
    normalized_fqdns = normalize_fqdns(fqdns)

    # Parse ports
    ports = [int(p.strip()) for p in args.ports.split(",")]

    # Ensure at least one check option is specified
    if not args.wp and not args.robots:
        print("Error: You must specify at least one check option (--wp or --robots).")
        sys.exit(1)

    # Perform checks based on user-specified options
    results = []
    for fqdn in normalized_fqdns:
        for port in ports:
            banner = grab_banner(fqdn, port)
            if banner == "No Response":
                continue
            result_line = f"{fqdn:<30} {port:<5} {banner:<20}"
            if args.wp:
                result_line += f"{check_wordpress(fqdn, port):<40}"
            if args.robots:
                result_line += f"{check_robots(fqdn, port):<40}"
            results.append(result_line)

    # Print results
    print("\n".join(results))

if __name__ == "__main__":
    main()
