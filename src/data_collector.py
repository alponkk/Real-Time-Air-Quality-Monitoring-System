"""
Air Quality Data Collector

This module handles data collection from various air quality APIs
and generates mock data when API keys are not available.
"""

import json
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

import requests
from loguru import logger

from config import config


class AirQualityDataCollector:
    """Collects air quality data from various APIs and mock sources"""
    
    def __init__(self):
        self.config = config
        self.session = requests.Session()
        self.session.timeout = self.config.api.request_timeout
        
        # Track API usage to avoid rate limits
        self.api_calls_count = {
            'openweather': 0,
            'airvisual': 0,
            'waqi': 0
        }
        
        # Mock data patterns for realistic simulation
        self.mock_patterns = {
            'New York': {'base_aqi': 45, 'variability': 20, 'seasonal_factor': 1.1},
            'London': {'base_aqi': 35, 'variability': 15, 'seasonal_factor': 1.0},
            'Tokyo': {'base_aqi': 40, 'variability': 25, 'seasonal_factor': 1.2},
            'Beijing': {'base_aqi': 85, 'variability': 40, 'seasonal_factor': 1.5},
            'Delhi': {'base_aqi': 120, 'variability': 60, 'seasonal_factor': 1.8},
            'Los Angeles': {'base_aqi': 55, 'variability': 30, 'seasonal_factor': 1.3},
            'Mexico City': {'base_aqi': 75, 'variability': 35, 'seasonal_factor': 1.4},
            'São Paulo': {'base_aqi': 50, 'variability': 25, 'seasonal_factor': 1.2}
        }

    def collect_all_cities_data(self) -> List[Dict]:
        """Collect air quality data for all configured cities"""
        all_data = []
        
        for city in self.config.data.cities:
            try:
                data = self.collect_city_data(
                    city['name'], 
                    city['country'], 
                    city['lat'], 
                    city['lon']
                )
                if data:
                    all_data.append(data)
                    logger.info(f"Collected data for {city['name']}, {city['country']}")
                else:
                    logger.warning(f"No data collected for {city['name']}, {city['country']}")
                    
                # Add delay to avoid hitting API rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting data for {city['name']}: {str(e)}")
                continue
        
        return all_data

    def collect_city_data(self, city: str, country: str, lat: float, lon: float) -> Optional[Dict]:
        """Collect air quality data for a specific city"""
        
        # Try real APIs first if keys are available
        if self.config.api.openweather_api_key:
            data = self._get_openweather_data(city, lat, lon)
            if data:
                data.update({'data_source': 'openweather', 'country': country})
                return data
        
        if self.config.api.airvisual_api_key:
            data = self._get_airvisual_data(city, country)
            if data:
                data.update({'data_source': 'airvisual'})
                return data
                
        if self.config.api.waqi_api_key:
            data = self._get_waqi_data(city)
            if data:
                data.update({'data_source': 'waqi', 'country': country})
                return data
        
        # Fallback to mock data
        logger.info(f"Using mock data for {city}, {country}")
        return self._generate_mock_data(city, country, lat, lon)

    def _get_openweather_data(self, city: str, lat: float, lon: float) -> Optional[Dict]:
        """Get air quality data from OpenWeatherMap API"""
        try:
            # Air pollution endpoint
            air_url = f"{self.config.api.openweather_base_url}/air_pollution"
            air_params = {
                'lat': lat,
                'lon': lon,
                'appid': self.config.api.openweather_api_key
            }
            
            # Weather endpoint
            weather_url = f"{self.config.api.openweather_base_url}/weather"
            weather_params = {
                'q': city,
                'appid': self.config.api.openweather_api_key,
                'units': 'metric'
            }
            
            # Make requests
            air_response = self._make_request(air_url, air_params)
            weather_response = self._make_request(weather_url, weather_params)
            
            if not air_response or not weather_response:
                return None
            
            self.api_calls_count['openweather'] += 2
            
            # Parse air quality data
            air_data = air_response['list'][0]
            weather_data = weather_response
            
            # Convert to our format
            return {
                'city': city,
                'latitude': lat,
                'longitude': lon,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'aqi': air_data['main']['aqi'] * 50,  # Scale 1-5 to AQI-like scale
                'aqi_category': self._get_aqi_category(air_data['main']['aqi'] * 50),
                'pm25': air_data['components'].get('pm2_5', 0),
                'pm10': air_data['components'].get('pm10', 0),
                'no2': air_data['components'].get('no2', 0),
                'so2': air_data['components'].get('so2', 0),
                'co': air_data['components'].get('co', 0),
                'o3': air_data['components'].get('o3', 0),
                'temperature': weather_data['main']['temp'],
                'humidity': weather_data['main']['humidity'],
                'pressure': weather_data['main']['pressure'],
                'wind_speed': weather_data.get('wind', {}).get('speed', 0),
                'wind_direction': weather_data.get('wind', {}).get('deg', 0),
                'data_quality': 'good'
            }
            
        except Exception as e:
            logger.error(f"Error fetching OpenWeather data for {city}: {str(e)}")
            return None

    def _get_airvisual_data(self, city: str, country: str) -> Optional[Dict]:
        """Get air quality data from AirVisual API"""
        try:
            url = f"{self.config.api.airvisual_base_url}/city"
            params = {
                'city': city,
                'country': country,
                'key': self.config.api.airvisual_api_key
            }
            
            response = self._make_request(url, params)
            if not response:
                return None
                
            self.api_calls_count['airvisual'] += 1
            
            data = response['data']
            current = data['current']
            
            return {
                'city': city,
                'country': country,
                'latitude': data['location']['coordinates'][1],
                'longitude': data['location']['coordinates'][0],
                'timestamp': current['pollution']['ts'],
                'aqi': current['pollution']['aqius'],
                'aqi_category': self._get_aqi_category(current['pollution']['aqius']),
                'pm25': current['pollution'].get('p2', {}).get('v', 0),
                'pm10': current['pollution'].get('p1', {}).get('v', 0),
                'temperature': current['weather']['tp'],
                'humidity': current['weather']['hu'],
                'pressure': current['weather']['pr'],
                'wind_speed': current['weather']['ws'],
                'wind_direction': current['weather']['wd'],
                'data_quality': 'good'
            }
            
        except Exception as e:
            logger.error(f"Error fetching AirVisual data for {city}: {str(e)}")
            return None

    def _get_waqi_data(self, city: str) -> Optional[Dict]:
        """Get air quality data from World Air Quality Index API"""
        try:
            url = f"{self.config.api.waqi_base_url}/feed/{city}/"
            params = {'token': self.config.api.waqi_api_key}
            
            response = self._make_request(url, params)
            if not response or response['status'] != 'ok':
                return None
                
            self.api_calls_count['waqi'] += 1
            
            data = response['data']
            
            return {
                'city': city,
                'latitude': data['city']['geo'][0],
                'longitude': data['city']['geo'][1],
                'timestamp': data['time']['iso'],
                'aqi': data['aqi'],
                'aqi_category': self._get_aqi_category(data['aqi']),
                'pm25': data['iaqi'].get('pm25', {}).get('v', 0),
                'pm10': data['iaqi'].get('pm10', {}).get('v', 0),
                'no2': data['iaqi'].get('no2', {}).get('v', 0),
                'so2': data['iaqi'].get('so2', {}).get('v', 0),
                'co': data['iaqi'].get('co', {}).get('v', 0),
                'o3': data['iaqi'].get('o3', {}).get('v', 0),
                'temperature': data['iaqi'].get('t', {}).get('v', 20),
                'humidity': data['iaqi'].get('h', {}).get('v', 50),
                'pressure': data['iaqi'].get('p', {}).get('v', 1013),
                'wind_speed': data['iaqi'].get('w', {}).get('v', 0),
                'data_quality': 'good'
            }
            
        except Exception as e:
            logger.error(f"Error fetching WAQI data for {city}: {str(e)}")
            return None

    def _generate_mock_data(self, city: str, country: str, lat: float, lon: float) -> Dict:
        """Generate realistic mock air quality data"""
        
        # Get city-specific patterns or use defaults
        pattern = self.mock_patterns.get(city, {
            'base_aqi': 50, 
            'variability': 25, 
            'seasonal_factor': 1.0
        })
        
        # Add some time-based variation (worse in morning/evening rush hours)
        hour = datetime.now().hour
        time_factor = 1.0
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
            time_factor = 1.3
        elif 2 <= hour <= 5:  # Early morning - cleaner
            time_factor = 0.7
        
        # Generate base AQI with variation
        base_aqi = pattern['base_aqi'] * pattern['seasonal_factor'] * time_factor
        aqi = max(1, int(base_aqi + random.uniform(-pattern['variability'], pattern['variability'])))
        
        # Generate related pollutant values based on AQI
        pm25 = max(0, aqi * 0.6 + random.uniform(-10, 10))
        pm10 = max(0, pm25 * 1.5 + random.uniform(-5, 15))
        no2 = max(0, aqi * 0.4 + random.uniform(-15, 15))
        so2 = max(0, aqi * 0.2 + random.uniform(-5, 10))
        co = max(0, aqi * 0.8 + random.uniform(-20, 20))
        o3 = max(0, aqi * 0.5 + random.uniform(-10, 10))
        
        # Generate weather data
        temperature = 20 + random.uniform(-15, 15)  # °C
        humidity = 50 + random.uniform(-30, 40)     # %
        pressure = 1013 + random.uniform(-20, 20)  # hPa
        wind_speed = random.uniform(0, 15)         # m/s
        wind_direction = random.randint(0, 360)    # degrees
        
        return {
            'city': city,
            'country': country,
            'latitude': lat,
            'longitude': lon,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'aqi': aqi,
            'aqi_category': self._get_aqi_category(aqi),
            'pm25': round(pm25, 2),
            'pm10': round(pm10, 2),
            'no2': round(no2, 2),
            'so2': round(so2, 2),
            'co': round(co, 2),
            'o3': round(o3, 2),
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'pressure': round(pressure, 1),
            'wind_speed': round(wind_speed, 1),
            'wind_direction': wind_direction,
            'data_source': 'mock',
            'data_quality': 'synthetic'
        }

    def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        for attempt in range(self.config.api.max_retries):
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.config.api.max_retries - 1:
                    time.sleep(self.config.api.retry_delay)
                else:
                    logger.error(f"All request attempts failed for {url}")
                    return None

    def _get_aqi_category(self, aqi: Union[int, float]) -> str:
        """Convert AQI value to category string"""
        aqi = int(aqi)
        
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            return "Unhealthy"
        elif aqi <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"

    def get_api_usage_stats(self) -> Dict:
        """Get API usage statistics"""
        return {
            'openweather_calls': self.api_calls_count['openweather'],
            'airvisual_calls': self.api_calls_count['airvisual'],
            'waqi_calls': self.api_calls_count['waqi'],
            'total_calls': sum(self.api_calls_count.values())
        }

    def check_alert_conditions(self, data: Dict) -> Optional[Dict]:
        """Check if air quality data triggers any alerts"""
        aqi = data.get('aqi', 0)
        city = data.get('city', 'Unknown')
        country = data.get('country', 'Unknown')
        
        alert = None
        thresholds = self.config.data.aqi_alert_thresholds
        
        if aqi >= thresholds['hazardous']:
            alert = {
                'city': city,
                'country': country,
                'alert_type': 'hazardous',
                'alert_level': 'emergency',
                'message': f'HAZARDOUS air quality in {city}! AQI: {aqi}. Avoid outdoor activities.',
                'aqi_value': aqi,
                'threshold_exceeded': 'aqi',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        elif aqi >= thresholds['very_unhealthy']:
            alert = {
                'city': city,
                'country': country,
                'alert_type': 'very_unhealthy',
                'alert_level': 'danger',
                'message': f'VERY UNHEALTHY air quality in {city}! AQI: {aqi}. Everyone should avoid outdoor activities.',
                'aqi_value': aqi,
                'threshold_exceeded': 'aqi',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        elif aqi >= thresholds['unhealthy']:
            alert = {
                'city': city,
                'country': country,
                'alert_type': 'unhealthy',
                'alert_level': 'warning',
                'message': f'UNHEALTHY air quality in {city}! AQI: {aqi}. Sensitive groups should avoid outdoor activities.',
                'aqi_value': aqi,
                'threshold_exceeded': 'aqi',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        return alert 