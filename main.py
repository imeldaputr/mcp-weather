from mcp.server.fastmcp import FastMCP
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Weather", dependencies=["httpx"])

API_KEY = os.getenv("ACCUWEATHER_API_KEY")
BASE_URL = os.getenv("ACCUWEATHER_BASE_URL")


@mcp.tool()
async def get_location_by_coordinates(latitude: float, longitude: float) -> str:
    """
    Get location information (City Name, Location Key) from latitude and longitude.
    Useful for 'dapatkan latlong' or reverse geocoding.
    """
    url = f"{BASE_URL}/locations/v1/cities/geoposition/search"
    params = {
        "apikey": API_KEY,
        "q": f"{latitude},{longitude}" # query
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
    location_key = data.get("Key")
    localized_name = data.get("LocalizedName")
    administrative_area = data.get("AdministrativeArea", {}).get("LocalizedName")
    country = data.get("Country", {}).get("LocalizedName")
    
    return f"Location: {localized_name}, {administrative_area}, {country}. Key: {location_key}"


@mcp.tool()
async def search_location(query: str) -> str:
    """
    Search for a location by name (city name) to get its Location Key.
    Useful for 'dapatkan nama kota' / finding the key for weather query.
    """
    url = f"{BASE_URL}/locations/v1/cities/search"
    params = {
        "apikey": API_KEY,
        "q": query
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
    if not data:
        return "No location found."
        
    top_match = data[0]
    location_key = top_match.get("Key")
    localized_name = top_match.get("LocalizedName")
    country = top_match.get("Country", {}).get("LocalizedName")
    
    return f"Found: {localized_name}, {country}. Key: {location_key}"


@mcp.tool()
async def get_current_weather(location_key: str) -> str:
    """
    Get current weather conditions for a specific Location Key.
    """
    url = f"{BASE_URL}/currentconditions/v1/{location_key}"
    params = {"apikey": API_KEY}
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
    if not data:
        return "No weather data available."
        
    weather = data[0]
    weather_text = weather.get("WeatherText")
    temp_value = weather.get("Temperature", {}).get("Metric", {}).get("Value")
    temp_unit = weather.get("Temperature", {}).get("Metric", {}).get("Unit")
    
    return f"Current Weather: {weather_text}, Temperature: {temp_value}°{temp_unit}"


@mcp.tool()
async def get_forecast(location_key: str, days: int = 5) -> str:
    """
    Get weather forecast for the next days (default 5).
    """
    # AccuWeather free tier usually supports 1 day, 5 days.
    # We will strictly use the 5 day endpoint from examples.py logic.
    url = f"{BASE_URL}/forecasts/v1/daily/5day/{location_key}"
    params = {
        "apikey": API_KEY,
        "metric": "true"
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
    forecasts = []
    headline = data.get("Headline", {}).get("Text", "No headline")
    forecasts.append(f"Forecast Headline: {headline}")
    
    for day in data.get("DailyForecasts", []):
        date = day.get("Date", "").split("T")[0]
        min_temp = day.get("Temperature", {}).get("Minimum", {}).get("Value")
        max_temp = day.get("Temperature", {}).get("Maximum", {}).get("Value")
        day_phrase = day.get("Day", {}).get("IconPhrase")
        forecasts.append(f"- {date}: {day_phrase}, Min: {min_temp}°C, Max: {max_temp}°C")
        
    return "\n".join(forecasts)


if __name__ == "__main__":
    print("Starting MCP Weather Application...")
    mcp.run()
    
