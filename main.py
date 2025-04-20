import yaml
import time
import aiohttp
import asyncio
from collections import defaultdict

# Function to load configuration from the YAML file
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Function to perform health checks
async def check_health(endpoint, session, domain):
    url = endpoint['url']
    method = endpoint.get('method')
    headers = endpoint.get('headers')
    body = endpoint.get('body')
    timeout = 14 # 1 second of buffer to account for asyncio.gather lag/ total execution time

    # Default method for request
    if not method:
        method = "GET"

    try:
        startTime = time.monotonic()
        response = None
        async with session.request(
            method, url, headers=headers, timeout=timeout, json=body
        ) as response:
            requestResponseTime = (time.monotonic() - startTime) * 1000 # need time in ms
            # print("ms" , requestResponseTime)
            if 200 <= response.status < 300 and requestResponseTime <= 500:
                return "UP", domain
            else:
                return "DOWN", domain
    except Exception:
        return "DOWN", domain

# Main function to monitor endpoints
async def monitor_endpoints(file_path):
    config = load_config(file_path)
    # error checking to make sure this is a valid filepath
    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})

    async with aiohttp.ClientSession() as session:
        while True:
            startTime = time.monotonic()
            requests = []
            for endpoint in config:
                domain = endpoint["url"].split("//")[-1]
                if ':' in domain:
                    domain = domain.split(":")[0]
                else:
                    domain = domain.split("/")[0]


                domain_stats[domain]["total"] += 1
                requests.append(check_health(endpoint, session, domain))

            results = await asyncio.gather(*requests)

            for result, domain in results:
                if result == "UP":
                    domain_stats[domain]["up"] += 1

            # Log cumulative availability percentages
            for domain, stats in domain_stats.items():
                availability = round(100 * stats["up"] / stats["total"])
                print(f"{domain} has {availability}% availability percentage")

            requestResponseTime = time.monotonic() - startTime
            if requestResponseTime < float(15): # sleep if we haven't met 15 seeconds
                time.sleep(float(15)-requestResponseTime)
            requestResponseTime = time.monotonic() - startTime
            # print("seconds:", requestResponseTime)
            print("---")

# Entry point of the program
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python monitor.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]
    try:
        asyncio.get_event_loop().run_until_complete(monitor_endpoints(config_file))
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")