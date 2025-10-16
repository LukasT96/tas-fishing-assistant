"""

Tools Model

Used for search information from external source (Internet)
when out of scope of RAG model.

"""

import os
import yaml
import requests
import json
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
        
        # Legal size check settings
        self.legal_size_enabled = self.tools_config.get('legal_size_check', {}).get('enabled', True)
        
        # Load legal size limits from tas_fishing_species.json
        self.legal_sizes = self._load_legal_sizes()
        
        # Weather API settings
        self.weather_config = self.tools_config.get('weather_api', {})
        self.weather_enabled = self.weather_config.get('enable', False)
        self.weather_provider = self.weather_config.get('provider', 'openweathermap')
        
        # Common Tasmania fishing locations
        self.fishing_locations = [
            "Hobart", "Launceston", "Devonport", "Burnie", "Derwent River",
            "Tamar River", "Great Lake", "Lake St Clair", "Gordon River",
            "St Helens", "Bicheno", "Swansea", "Strahan", "Port Arthur"
        ]
        
        if self.weather_enabled:
            self.weather_api_key = os.getenv(
                self.weather_config.get('api_key_env', 'WEATHER_API_KEY')
            )
            self.weather_base_url = self.weather_config.get('base_url', '')
    
    def _load_legal_sizes(self) -> Dict[str, float]:
        """
        Load legal size limits from tas_fishing_species.json
        
        This method dynamically loads legal size information from the JSON file,
        making it easy to maintain and update without changing code.
        
        **How it works:**
        1. Reads tas_fishing_species.json and extracts "Minimum size" field
        2. Parses size strings (e.g., "35cm", "120mm") using regex
        3. Converts all sizes to centimeters
        4. Creates aliases for common name variations
        5. Adds manual overrides for species not in JSON (e.g., freshwater fish)
        
        **To add a new species:**
        - If in JSON: Just ensure "Minimum size" field has a value like "35cm" or "120mm"
        - If not in JSON: Add to the manual_sizes dictionary below
        
        Returns:
            Dictionary mapping species names to minimum legal sizes in cm
        """
        species_file = "data/tas_fishing_species.json"
        legal_sizes = {}
        
        try:
            with open(species_file, 'r', encoding='utf-8') as f:
                species_data = json.load(f)
            
            # Parse the JSON and extract minimum sizes
            for species_name, info in species_data.items():
                min_size = info.get("Minimum size")
                
                # Skip if no minimum size specified
                if not min_size or min_size in [None, ""]:
                    continue
                
                # Parse the minimum size string
                # Examples:
                # "120 mm from Arthur River east to Musselroe Point, 138 mm for all other waters."
                # "All waters (except King and Flinders Islands): Minimum size 35cm , maximum size 40cm"
                # "Northern Zone - male 110mm, female 120mm"
                
                # Normalize species name for lookup
                species_key = species_name.lower().replace(" - ", " ").strip()
                
                # Extract numeric size (look for first occurrence of digits followed by mm or cm)
                import re
                
                # Try to find mm or cm measurements
                cm_match = re.search(r'(\d+(?:\.\d+)?)\s*cm', min_size.lower())
                mm_match = re.search(r'(\d+(?:\.\d+)?)\s*mm', min_size.lower())
                
                if cm_match:
                    size_cm = float(cm_match.group(1))
                    legal_sizes[species_key] = size_cm
                elif mm_match:
                    size_mm = float(mm_match.group(1))
                    size_cm = size_mm / 10.0  # Convert mm to cm
                    legal_sizes[species_key] = size_cm
            
            # Add aliases for common names
            if "abalone blacklip" in legal_sizes:
                legal_sizes["blacklip abalone"] = legal_sizes["abalone blacklip"]
                legal_sizes["abalone"] = legal_sizes["abalone blacklip"]
            
            if "abalone greenlip" in legal_sizes:
                legal_sizes["greenlip abalone"] = legal_sizes["abalone greenlip"]
            
            if "trout brown" in legal_sizes:
                legal_sizes["brown trout"] = legal_sizes["trout brown"]
            
            if "salmon atlantic" in legal_sizes:
                legal_sizes["atlantic salmon"] = legal_sizes["salmon atlantic"]
            
            if "rock lobster southern" in legal_sizes or "rock lobster eastern" in legal_sizes:
                # Use the northern zone male size as default (110mm = 11cm)
                legal_sizes["rock lobster"] = 11.0
                legal_sizes["southern rock lobster"] = 11.0
                legal_sizes["eastern rock lobster"] = 11.0
            
            if "flathead sand" in legal_sizes:
                legal_sizes["sand flathead"] = legal_sizes["flathead sand"]
            
            # Add manual overrides for species not in JSON or with null values
            # (e.g., freshwater species managed by Inland Fisheries Service)
            manual_sizes = {
                "brown trout": 25.0,
                "rainbow trout": 25.0,
                "atlantic salmon": 30.0,
                "trout brown": 25.0,
                "salmon atlantic": 30.0
            }
            
            for species, size in manual_sizes.items():
                if species not in legal_sizes:
                    legal_sizes[species] = size
            
            print(f"Loaded {len(legal_sizes)} species with legal size limits from {species_file}")
            
        except FileNotFoundError:
            print(f"Warning: {species_file} not found. Using empty legal sizes database.")
        except json.JSONDecodeError as e:
            print(f"Error parsing {species_file}: {e}. Using empty legal sizes database.")
        except Exception as e:
            print(f"Unexpected error loading legal sizes: {e}. Using empty legal sizes database.")
        
        return legal_sizes
    
    def check_legal_size(self, species: str, length_cm: float) -> Dict:
        """
        Check if a caught fish meets legal minimum size requirements in Tasmania.
        
        Args:
            species: Fish species name (e.g., 'brown trout', 'rainbow trout')
            length_cm: Length of the caught fish in centimeters
            
        Returns:
            Dict containing:
                - success: bool
                - legal: bool (whether the fish is legal to keep)
                - species: str (normalized species name)
                - length_cm: float (provided length)
                - legal_size_cm: float (minimum legal size)
                - difference_cm: float (how much over/under the limit)
                - message: str (human-readable result)
        """
        if not self.legal_size_enabled:
            return {
                "success": False,
                "error": "Legal size check tool is disabled",
                "message": "Legal size check tool is currently disabled in configuration"
            }
        
        # Normalize species name (lowercase, strip whitespace)
        species_normalized = species.lower().strip()
        
        # Check if species is supported
        if species_normalized not in self.legal_sizes:
            available_species = ", ".join(self.legal_sizes.keys())
            return {
                "success": False,
                "error": f"Unknown species: {species}",
                "message": f"I don't have legal size information for '{species}'. Available species: {available_species}",
                "available_species": list(self.legal_sizes.keys())
            }
        
        # Validate length
        if length_cm <= 0:
            return {
                "success": False,
                "error": "Invalid length",
                "message": f"Length must be greater than 0. You provided: {length_cm} cm"
            }
        
        # Get legal size for species
        legal_size = self.legal_sizes[species_normalized]
        
        # Check if legal to keep
        is_legal = length_cm >= legal_size
        difference = length_cm - legal_size
        
        # Format measurement note for rock lobster and abalone
        measurement_note = ""
        if species_normalized == "rock lobster":
            measurement_note = " (carapace length)"
        elif species_normalized == "abalone":
            measurement_note = " (shell length)"
        
        # Create detailed message
        if is_legal:
            message = f"✅ **LEGAL TO KEEP**\n\n"
            message += f"• Species: {species_normalized.title()}\n"
            message += f"• Your catch: {length_cm} cm{measurement_note}\n"
            message += f"• Legal minimum: {legal_size} cm\n"
            message += f"• Over limit by: {difference:.1f} cm\n\n"
            message += f"This fish meets the legal size requirement and may be kept (subject to bag limits)."
        else:
            message = f"❌ **MUST BE RELEASED**\n\n"
            message += f"• Species: {species_normalized.title()}\n"
            message += f"• Your catch: {length_cm} cm{measurement_note}\n"
            message += f"• Legal minimum: {legal_size} cm\n"
            message += f"• Under limit by: {abs(difference):.1f} cm\n\n"
            message += f"This fish is undersized and must be returned to the water immediately with care."
        
        return {
            "success": True,
            "legal": is_legal,
            "species": species_normalized,
            "length_cm": length_cm,
            "legal_size_cm": legal_size,
            "difference_cm": difference,
            "message": message
        }
    
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
        
        if self.legal_size_enabled:
            tools.append("check_legal_size")
        
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
        if tool_name == "check_legal_size":
            return self.check_legal_size(
                species=kwargs.get("species", ""),
                length_cm=kwargs.get("length_cm", 0)
            )
        elif tool_name == "get_fishing_weather":
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
        
        if self.legal_size_enabled:
            descriptions.append({
                "type": "function",
                "function": {
                    "name": "check_legal_size",
                    "description": "Check if a caught fish meets the legal minimum size requirements in Tasmania. Returns whether the fish is legal to keep or must be released. Use this when users ask about legal sizes, whether they can keep a fish, or if a specific length is legal.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "species": {
                                "type": "string",
                                "description": "The fish species name (e.g., 'brown trout', 'rainbow trout', 'atlantic salmon', 'rock lobster', 'abalone')",
                                "enum": ["brown trout", "rainbow trout", "atlantic salmon", "rock lobster", "abalone"]
                            },
                            "length_cm": {
                                "type": "number",
                                "description": "The length of the caught fish in centimeters",
                                "minimum": 0
                            }
                        },
                        "required": ["species", "length_cm"]
                    }
                }
            })
        
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
                                "description": "Tasmania fishing location name"
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