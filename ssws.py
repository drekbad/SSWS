import requests
from termcolor import colored
import sys

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

def main(input_file):
    # Read the input file containing FQDNs
    with open(input_file, "r") as file:
        fqdns = [line.strip() for line in file if line.strip()]
    
    # Normalize and prepare FQDN list
    normalized_fqdns = normalize_fqdns(fqdns)

    # Check each FQDN for WordPress
    results = []
    for fqdn in normalized_fqdns:
        result = check_wordpress(fqdn)
        results.append(f"{fqdn:<30} {result}")

    # Print results
    print("\n".join(results))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_wp.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    main(input_file)
