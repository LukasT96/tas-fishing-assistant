"""

Tools Model

Used for search information from external source (Internet)
when out of scope of RAG model.

"""

import os
import yaml
import requests
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()

class ToolsModel:
    """Collection of tools for Tasmania Fishing Chatbot"""
    def __init__(self, config_path: str = "config.yml"):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Load tools configurations
        self.tools_config = self.config.get('tools', {})
        
        # Weather API settings
        self.weather_config = self.tools_config.get('weather_api', {})
        self.weather_enabled = self.weather_config.get('enable', False)
        self.weather_provider = self.weather_config.get('provider', 'openweathermap')
        
        if self.weather_enabled:
            self.weather_api_key = os.getenv(
                self.weather_config.get('api_key_env', 'WEATHER_API_KEY')
            )
            self.base_url = self.weather_config.get('base_url', '')
    
    
    def get_fishing_weather(self, location: str, days: int = 1) -> Dict:
        if not self.weather_enabled:
            return {
                "success": False,
                "error": "Weather API is not enabled",
                "message": "Weather tool is currently disabled in configuration"
            }
        
        if not self.weather_api_key:
            return {
                "success": False,
                "error": "Weather API key not found",
                "message": "Please add WEATHER_API_KEY to your .env file"
            }
            
        try:
            # Format location for API
            location_query = f"{location},Tasmania,AU"
            
            if self.weather_provider == "openweathermap":
                return self._get_openweathermap_forecast(location_query, location, days)
            elif self.weather_provider == "weatherapi":
                return self._get_weatherapi_forecast(location_query, location, days)
            else:
                return {
                    "success": False,
                    "error": "Unknown weather provider",
                    "message": f"Weather provider '{self.weather_provider}' not supported"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to fetch weather data: {str(e)}"
            }
            
    def _get_openweathermap_forecast(self, location_query: str, location: str, days: int) -> Dict:
        """Get forecast from OpenWeatherMap API"""
        
        # OpenWeatherMap forecast endpoint (5 day / 3 hour forecast)
        url = f"{self.weather_base_url}/forecast"
        params = {
            "q": location_query,
            "appid": self.weather_api_key,
            "units": "metric",  # Celsius
            "cnt": min(days * 8, 40)  # 8 forecasts per day (3-hour intervals)
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse daily summaries
        forecasts = []
        daily_data = {}
        
        for item in data.get('list', []):
            date = item['dt_txt'].split()[0]
            
            if date not in daily_data:
                daily_data[date] = {
                    'temps': [],
                    'conditions': [],
                    'wind_speeds': [],
                    'rain': 0,
                    'humidity': []
                }
            
            daily_data[date]['temps'].append(item['main']['temp'])
            daily_data[date]['conditions'].append(item['weather'][0]['description'])
            daily_data[date]['wind_speeds'].append(item['wind']['speed'])
            daily_data[date]['humidity'].append(item['main']['humidity'])
            
            if 'rain' in item:
                daily_data[date]['rain'] += item['rain'].get('3h', 0)
        
        # Create daily summaries
        for date, day_data in list(daily_data.items())[:days]:
            avg_temp = sum(day_data['temps']) / len(day_data['temps'])
            max_temp = max(day_data['temps'])
            min_temp = min(day_data['temps'])
            avg_wind = sum(day_data['wind_speeds']) / len(day_data['wind_speeds'])
            avg_humidity = sum(day_data['humidity']) / len(day_data['humidity'])
            
            # Get most common condition
            conditions = max(set(day_data['conditions']), key=day_data['conditions'].count)
            
            forecasts.append({
                "date": date,
                "temp_avg_c": round(avg_temp, 1),
                "temp_max_c": round(max_temp, 1),
                "temp_min_c": round(min_temp, 1),
                "conditions": conditions,
                "wind_speed_kmh": round(avg_wind * 3.6, 1),  # Convert m/s to km/h
                "rainfall_mm": round(day_data['rain'], 1),
                "humidity_percent": round(avg_humidity, 0)
            })
        
        # Assess fishing conditions
        fishing_assessment = self._assess_fishing_conditions(forecasts[0] if forecasts else None)
        
        # Create message
        message = self._format_weather_message(location, forecasts, fishing_assessment)
        
        return {
            "success": True,
            "location": location,
            "forecasts": forecasts,
            "fishing_conditions": fishing_assessment['rating'],
            "message": message
        }
        
    def _assess_fishing_conditions(self, forecast: Optional[Dict]) -> Dict:
        """
        Assess if weather is good for fishing
        
        Returns:
            Dict with rating and explanation
        """
        if not forecast:
            return {
                "rating": "Unknown",
                "explanation": "No forecast data available"
            }
        
        score = 0
        factors = []
        
        # Temperature (ideal: 10-25°C)
        temp = forecast['temp_avg_c']
        if 10 <= temp <= 25:
            score += 3
            factors.append("✅ Good temperature")
        elif 5 <= temp < 10 or 25 < temp <= 30:
            score += 1
            factors.append("⚠️ Moderate temperature")
        else:
            factors.append("❌ Extreme temperature")
        
        # Wind (ideal: < 20 km/h)
        wind = forecast['wind_speed_kmh']
        if wind < 15:
            score += 3
            factors.append("✅ Light winds")
        elif 15 <= wind < 25:
            score += 1
            factors.append("⚠️ Moderate winds")
        else:
            factors.append("❌ Strong winds")
        
        # Rain (ideal: < 5mm)
        rain = forecast['rainfall_mm']
        if rain < 2:
            score += 2
            factors.append("✅ Dry conditions")
        elif 2 <= rain < 10:
            score += 1
            factors.append("⚠️ Light rain possible")
        else:
            factors.append("❌ Heavy rain expected")
        
        # Determine rating
        if score >= 7:
            rating = "Excellent"
            emoji = "🎣✨"
        elif score >= 5:
            rating = "Good"
            emoji = "🎣"
        elif score >= 3:
            rating = "Fair"
            emoji = "⚠️"
        else:
            rating = "Poor"
            emoji = "❌"
        
        return {
            "rating": rating,
            "emoji": emoji,
            "score": score,
            "factors": factors
        }
    
    def _format_weather_message(self, location: str, forecasts: List[Dict], assessment: Dict) -> str:
        """Format weather information into readable message"""
        
        if not forecasts:
            return f"❌ No weather data available for {location}"
        
        message_parts = [
            f"🌤️ **Weather Forecast for {location}, Tasmania**\n",
            f"**Fishing Conditions:** {assessment['emoji']} {assessment['rating']}\n"
        ]
        
        for i, forecast in enumerate(forecasts, 1):
            day_label = "Today" if i == 1 else f"Day {i}"
            
            message_parts.append(f"\n**{day_label} ({forecast['date']}):**")
            message_parts.append(f"• Temperature: {forecast['temp_min_c']}°C - {forecast['temp_max_c']}°C (avg {forecast['temp_avg_c']}°C)")
            message_parts.append(f"• Conditions: {forecast['conditions'].title()}")
            message_parts.append(f"• Wind: {forecast['wind_speed_kmh']} km/h")
            message_parts.append(f"• Rainfall: {forecast['rainfall_mm']} mm")
            message_parts.append(f"• Humidity: {forecast['humidity_percent']}%")
        
        # Add assessment factors
        message_parts.append("\n**Assessment:**")
        for factor in assessment['factors']:
            message_parts.append(f"• {factor}")
        
        return "\n".join(message_parts)
    
    def get_available_tools(self) -> List[str]:
        """Return list of available tool names"""
        tools = []
        
        if self.weather_enabled:
            tools.append("get_fishing_weather")
        
        return tools
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict:
        """
        Generic tool caller
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution results
        """
        if tool_name == "get_fishing_weather":
            return self.get_fishing_weather(
                location=kwargs.get("location", ""),
                days=kwargs.get("days", 1)
            )
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "available_tools": self.get_available_tools()
            }
    
    def get_tool_descriptions(self) -> List[Dict]:
        """Get OpenAI-style function descriptions for LLM tool calling"""
        descriptions = []
        
        if self.weather_enabled:
            descriptions.append({
                "type": "function",
                "function": {
                    "name": "get_fishing_weather",
                    "description": "Get weather forecast and fishing conditions for locations in Tasmania. Use this when users ask about weather, fishing conditions, or planning fishing trips.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Tasmania fishing location name",
                                "enum": self.fishing_locations
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to forecast (1-3)",
                                "minimum": 1,
                                "maximum": 3,
                                "default": 1
                            }
                        },
                        "required": ["location"]
                    }
                }
            })
        
        return descriptions