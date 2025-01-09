import requests
from termcolor import colored
import sys
import argparse

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

def check_wordpress(fqdn):
    """
    Check if a given FQDN's /wp-login.php page is a WordPress login page.
    """
    url = f"http://{fqdn}/wp-login.php"
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
    except requests.RequestException:
        return colored("No WordPress instance found.", "red")

def check_robots(fqdn):
    """
    Check if a given FQDN has a robots.txt file and contains "User-agent:" or "Disallow:".
    """
    url = f"http://{fqdn}/robots.txt"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            content = response.text.lower()
            if "user-agent:" in content or "disallow:" in content:
                return colored("robots.txt found!", "green")
        return colored("No robots.txt found.", "red")
    except requests.RequestException:
        return colored("No robots.txt found.", "red")

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
    
    args = parser.parse_args()
    
    # Read the input file containing FQDNs
    with open(args.input, "r") as file:
        fqdns = [line.strip() for line in file if line.strip()]
    
    # Normalize and prepare FQDN list
    normalized_fqdns = normalize_fqdns(fqdns)

    # Ensure at least one check option is specified
    if not args.wp and not args.robots:
        print("Error: You must specify at least one check option (--wp or --robots).")
        sys.exit(1)

    # Perform checks based on user-specified options
    results = []
    for fqdn in normalized_fqdns:
        result_line = f"{fqdn:<30}"
        if args.wp:
            result_line += f"{check_wordpress(fqdn)}"
        if args.robots:
            if args.wp:
                result_line += " | "
            result_line += f"{check_robots(fqdn)}"
        results.append(result_line)

    # Print results
    print("\n".join(results))

if __name__ == "__main__":
    main()
