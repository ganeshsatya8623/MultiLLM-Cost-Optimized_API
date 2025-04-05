import yaml
import httpx
import asyncio
from utils import estimate_tokens_and_cost

# Load providers from YAML config
def load_providers():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Validate configuration
    for provider in config["providers"]:
        required_keys = ["name", "api_key", "endpoint", "cost_per_1k_tokens"]
        for key in required_keys:
            if key not in provider:
                raise ValueError(f"Missing required key '{key}' in provider configuration: {provider}")
    
    return sorted(config["providers"], key=lambda x: x["cost_per_1k_tokens"])  # sort by cost

providers = load_providers()

async def call_provider(provider, prompt):
    try:
        headers = {"Authorization": f"Bearer {provider['api_key']}"}
        payload = {"prompt": prompt}

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(provider["endpoint"], json=payload, headers=headers)
            res.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)

            data = res.json()
            response_text = data.get("response") or data.get("choices", [{}])[0].get("text", "")
            if not response_text:
                print(f"No response text found for provider {provider['name']}. Response data: {data}")
                return None
            
            token_count, cost = estimate_tokens_and_cost(response_text, provider["cost_per_1k_tokens"])
            return {
                "modelUsed": provider["name"],
                "cost": cost,
                "tokens": token_count,
                "response": response_text
            }
    except httpx.HTTPStatusError as e:
        print(f"HTTP error with {provider['name']}: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"Error with {provider['name']}: {e}")
    return None

async def route_request(prompt):
    tasks = []
    for provider in providers:
        for attempt in range(2):  # Try twice per provider
            tasks.append(call_provider(provider, prompt))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            print(f"Error during request: {result}")
        elif result:
            return result
    
    raise Exception("All providers failed")

# Example usage
async def main():
    prompt = "What is the capital of France?"
    try:
        result = await route_request(prompt)
        print(result)
    except Exception as e:
        print(f"Failed to get a response: {e}")

if __name__ == "__main__":
    asyncio.run(main()
