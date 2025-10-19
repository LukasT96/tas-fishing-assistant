"""

Tools Model

Used for search information from external source (Internet)
when out of scope of RAG model.

"""

import os
import re
import json
import yaml
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from dotenv import load_dotenv

from src.prompts import TOOL_ANSWER_PROMPTS, TOOL_ERROR_MESSAGES, TOOL_DESCRIPTIONS


class ToolsModel:
    """Collection of tools for Tasmania Fishing Chatbot"""
    def __init__(self, config_path: str = "config.yml"):
        load_dotenv()
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Load tools configurations
        self.tools_config = self.config.get('tools', {})
        
        # Initialize weather tool
        self._init_weather_tool()
        
    
    def _init_weather_tool(self):
        """Initialize weather API settings"""
        self.weather_config = self.tools_config.get('weather_api', {})
        self.weather_enabled = self.weather_config.get('enable', True)
        self.weather_provider = self.weather_config.get('provider', 'openweathermap')
        
        if self.weather_enabled:
            # Get API key from environment variable
            api_key_env_var = self.weather_config.get('api_key_env', 'WEATHER_API_KEY')
            self.weather_api_key = os.getenv(api_key_env_var)
            
            # Get base URL from config (with fallback)
            self.weather_base_url = self.weather_config.get(
                'base_url', 
                'https://api.openweathermap.org/data/2.5'
            )
        else:
            self.weather_api_key = None
            self.weather_base_url = None
    
    
    # --- Weather ---
    def get_fishing_weather(self, location: str, days: int = 5) -> Dict:
            """
            Get weather forecast and fishing conditions for multiple days
            
            Args:
                location: Tasmania location name
                days: Number of days to forecast (1-5, default 5)
                
            Returns:
                Dict with forecast data and fishing recommendations
            """
            if not self.weather_enabled:
                return self._err("get_fishing_weather", "weather_disabled", "Weather API disabled")
            
            if not self.weather_api_key:
                return self._err("get_fishing_weather", "no_api_key", TOOL_ERROR_MESSAGES['weather_error'])
            
            # Limit to 5 days (OpenWeatherMap free tier supports up to 5 days)
            days = min(max(days, 1), 5)
            
            try:
                # Format location for API
                location_query = f"{location},Tasmania,AU"
                
                if self.weather_provider == "openweathermap":
                    return self._get_openweathermap_forecast(location_query, location, days)
                else:
                    return self._err("get_fishing_weather", "weather_provider_error", TOOL_ERROR_MESSAGES['weather_error'])
                
            except Exception as e:
                print(f"Weather API error: {e}")
                return self._err("get_fishing_weather", "error", TOOL_ERROR_MESSAGES['weather_error'])
           
            
    def _get_openweathermap_forecast(self, location_query: str, location: str, days: int) -> Dict:
        """Fetch and process OpenWeatherMap forecast data"""
        url = f"{self.weather_base_url}/forecast"
        params = {
            "q": location_query,
            "appid": self.weather_api_key,
            "units": "metric",
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Get timezone offset from API
        tz_offset_sec = (data.get("city", {}) or {}).get("timezone", 0)
        tz_offset = timedelta(seconds=tz_offset_sec)

        # Group forecast data by local date
        daily_data = {}  # date_str -> accumulators
        for item in data.get("list", []):
            # Convert UTC timestamp to local time
            ts_utc = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            local_dt = ts_utc + tz_offset
            date = local_dt.date().isoformat()

            # Initialize daily accumulator
            daily_data.setdefault(date, {
                "temps": [], 
                "conditions": [], 
                "wind_speeds": [], 
                "rain": 0.0, 
                "humidity": []
            })
            
            # Accumulate data
            d = daily_data[date]
            d["temps"].append(item["main"]["temp"])
            d["conditions"].append(item["weather"][0]["description"])
            d["wind_speeds"].append(item["wind"]["speed"])
            d["humidity"].append(item["main"]["humidity"])
            if "rain" in item:
                d["rain"] += float(item["rain"].get("3h", 0.0))

        # Select days to return (starting from today)
        ordered_dates = sorted(daily_data.keys())
        now_local = datetime.now(timezone.utc) + tz_offset
        today_local = now_local.date().isoformat()
        
        # Get dates starting from today
        future_dates = [d for d in ordered_dates if d >= today_local]
        selected_dates = future_dates[:days]

        # Build daily summaries with fishing scores
        forecasts = []
        for date in selected_dates:
            d = daily_data[date]
            
            # Calculate averages
            avg_temp = sum(d["temps"]) / len(d["temps"])
            max_temp = max(d["temps"])
            min_temp = min(d["temps"])
            avg_wind = sum(d["wind_speeds"]) / len(d["wind_speeds"])
            avg_humidity = sum(d["humidity"]) / len(d["humidity"])
            conditions = max(set(d["conditions"]), key=d["conditions"].count)
            
            # Create daily forecast
            daily_forecast = {
                "date": date,
                "temp_avg_c": round(avg_temp, 1),
                "temp_max_c": round(max_temp, 1),
                "temp_min_c": round(min_temp, 1),
                "conditions": conditions,
                "wind_speed_kmh": round(avg_wind * 3.6, 1),  # m/s -> km/h
                "rainfall_mm": round(d["rain"], 1),
                "humidity_percent": round(avg_humidity, 0)
            }
            
            # Add fishing assessment for this day
            daily_forecast["fishing_score"] = self._calculate_fishing_score(daily_forecast)
            
            forecasts.append(daily_forecast)

        # Find best fishing day
        best_day = self._find_best_fishing_day(forecasts)
        
        # Overall assessment
        overall_assessment = self._assess_multi_day_forecast(forecasts, best_day)
        
        return self._ok("get_fishing_weather", {
            "location": location,
            "forecast_days": len(forecasts),
            "forecasts": forecasts,
            "best_fishing_day": best_day,
            "recommendation": overall_assessment
        })
    
    
    def _calculate_fishing_score(self, forecast: Dict) -> int:
        """
        Calculate fishing quality score (0-10) based on weather conditions
        
        Returns:
            int: Score from 0 (worst) to 10 (best)
        """
        score = 0
        
        # Temperature scoring (ideal: 10-25°C)
        temp = forecast['temp_avg_c']
        if 10 <= temp <= 25:
            score += 4  # Ideal temperature
        elif 5 <= temp < 10 or 25 < temp <= 30:
            score += 2  # Acceptable temperature
        elif 0 <= temp < 5 or 30 < temp <= 35:
            score += 1  # Marginal temperature
        # else: 0 points for extreme temperatures
        
        # Wind scoring (ideal: < 20 km/h)
        wind = forecast['wind_speed_kmh']
        if wind < 15:
            score += 3  # Light winds - ideal
        elif 15 <= wind < 25:
            score += 2  # Moderate winds - acceptable
        elif 25 <= wind < 35:
            score += 1  # Strong winds - challenging
        # else: 0 points for very strong winds
        
        # Rain scoring (ideal: < 5mm)
        rain = forecast['rainfall_mm']
        if rain < 2:
            score += 3  # Dry - ideal
        elif 2 <= rain < 10:
            score += 2  # Light rain - acceptable
        elif 10 <= rain < 20:
            score += 1  # Moderate rain - marginal
        # else: 0 points for heavy rain
        
        return min(score, 10)  # Cap at 10
    
    
    def _find_best_fishing_day(self, forecasts: List[Dict]) -> Dict:
        """Find the best day for fishing based on scores"""
        if not forecasts:
            return None
        
        # Find day with highest fishing score
        best = max(forecasts, key=lambda f: f['fishing_score'])
        
        # Create readable assessment
        score = best['fishing_score']
        if score >= 8:
            rating = "Excellent"
            emoji = "🎣✨"
        elif score >= 6:
            rating = "Good"
            emoji = "🎣"
        elif score >= 4:
            rating = "Fair"
            emoji = "⚠️"
        else:
            rating = "Poor"
            emoji = "❌"
        
        return {
            "date": best['date'],
            "score": score,
            "rating": rating,
            "emoji": emoji,
            "temp_c": best['temp_avg_c'],
            "wind_kmh": best['wind_speed_kmh'],
            "rain_mm": best['rainfall_mm'],
            "conditions": best['conditions']
        }
   
   
    def _assess_multi_day_forecast(self, forecasts: List[Dict], best_day: Dict) -> str:
        """Generate human-readable recommendation for multi-day forecast"""
        if not forecasts or not best_day:
            return "No forecast data available"
        
        avg_score = sum(f['fishing_score'] for f in forecasts) / len(forecasts)
        
        if avg_score >= 7:
            outlook = "Great week ahead for fishing!"
        elif avg_score >= 5:
            outlook = "Generally good conditions expected"
        elif avg_score >= 3:
            outlook = "Mixed conditions throughout the period"
        else:
            outlook = "Challenging conditions expected"
        
        return f"{outlook} Best day: {best_day['date']} ({best_day['rating']})"
         
        
    def _assess_fishing_conditions(self, forecast: Optional[Dict]) -> Dict:
        """
        Legacy method - Assess if weather is good for fishing (single day)
        Kept for backward compatibility
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
    
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict:
        """Call a tool by name with parameters"""
        if tool_name == "get_fishing_weather":
            return self.get_fishing_weather(
                location=kwargs.get("location", "Hobart"),
                days=kwargs.get("days", 5)
            )
            
        return self._err(tool_name, "unknown_tool", f"Unknown tool: {tool_name}")
    
    
    def get_tool_descriptions(self) -> List[Dict]:
        """Get function descriptions for LLM tool calling"""
        return TOOL_DESCRIPTIONS
    
    
    def _ok(self, tool: str, data: dict) -> Dict:
        """Return success response"""
        return {"success": True, "tool": tool, "data": data}


    def _err(self, tool: str, code: str, detail: str) -> Dict:
        """Return error response"""
        return {"success": False, "tool": tool, "error": {"code": code, "detail": detail}}