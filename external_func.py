import aiohttp

async def get_current_temperature_async(town: str, api_key: str):

    api_url = f"http://api.openweathermap.org/data/2.5/weather?q={town}&units=metric&appid={api_key}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url) as response:
                if response.status != 200:
                    error_message = await response.json()
                    return None, error_message.get("message", "Unknown error")
                data = await response.json()
                current_temperature = data['main']['temp']
                return current_temperature, None
        except aiohttp.ClientError as e:
            # Ошибки вида таймаута, DNS и т.д.
            return None, str(e)

async def fetch_product_calories(product_name: str) -> float:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://world.openfoodfacts.org/cgi/search.pl",
            params={"search_terms": product_name, "search_simple": 1, "action": "process", "json": 1}
        ) as response:
            if response.status == 200:
                data = await response.json()
                products = data.get("products", [])
                if products:
                    product = products[0]
                    calories = product.get("nutriments", {}).get("energy-kcal_100g", 0)
                    return calories
            return 0