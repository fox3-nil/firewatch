import requests

SERVER_URL = "http://10.125.161.153:8080"


def ping_server(server_url):
    """
    Sends a GET request to the specified server URL and returns 'pong' 
    if the connection is successful (HTTP status 200-299).

    Args:
        server_url (str): The URL of the server to ping.

    Returns:
        str: 'pong' if connected, or an error message otherwise.
    """
    
    # 1. Ensure the URL starts with http:// or https://
    if not server_url.startswith(('http://', 'https://')):
        server_url = 'https://' + server_url

    try:
        # 2. Send a simple GET request. 
        #    timeout=5 ensures the script doesn't hang indefinitely.
        response = requests.get(server_url, timeout=5)

        # 3. Check for a successful status code (200-299)
        if 200 <= response.status_code < 300:
            return "pong"
        else:
            # Server responded, but with an error status (e.g., 404, 500)
            return f"Server responded with status: {response.status_code}"

    except requests.exceptions.Timeout:
        return "Ping failed: Request timed out."
    except requests.exceptions.ConnectionError:
        return "Ping failed: Could not connect to the server."
    except requests.exceptions.RequestException as e:
        # Catch any other request errors (e.g., invalid URL)
        return f"Ping failed: An unexpected error occurred: {e}"

# --- Example Usage ---

# 1. A known good URL (should return 'pong')
GOOD_URL = "www.google.com"

# 2. A known bad URL (should return a connection error)
BAD_URL = "http://this-url-does-not-exist-012345.com"

# 3. A server that is up but returns a client-side error (e.g., 404)
#    (Use a test URL that is known to return 404 if available)
# HTTPBIN_URL = "https://httpbin.org/status/404" 


print(f"Pinging {GOOD_URL}...")
result_good = ping_server(GOOD_URL)
print(f"Result: {result_good}\n")

print(f"Pinging {SERVER_URL}...")
result_bad = ping_server(SERVER_URL)
print(f"Result: {result_bad}")
