"""
Configuration module for Air Quality Monitoring System
"""
import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class KafkaConfig:
    """Kafka configuration settings"""
    bootstrap_servers: str = "kafka:29092"
    air_quality_topic: str = "air-quality-data"
    alerts_topic: str = "air-quality-alerts"
    consumer_group: str = "air-quality-consumer-group"
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    session_timeout_ms: int = 30000
    max_poll_records: int = 500


@dataclass
class PostgresConfig:
    """PostgreSQL configuration settings"""
    host: str = "postgres"
    port: int = 5432
    database: str = "airquality"
    username: str = "airquality_user"
    password: str = "airquality_pass"
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"








@dataclass
class APIConfig:
    """API configuration for weather and air quality services"""
    # OpenWeatherMap API (free tier: 1000 calls/day)
    openweather_api_key: Optional[str] = None  # Get from: https://openweathermap.org/api
    openweather_base_url: str = "http://api.openweathermap.org/data/2.5"
    
    # AirVisual API (free tier: 10000 calls/month)
    airvisual_api_key: Optional[str] = None  # Get from: https://www.iqair.com/air-pollution-data-api
    airvisual_base_url: str = "http://api.airvisual.com/v2"
    
    # World Air Quality Index API (free)
    waqi_api_key: Optional[str] = None  # Get from: https://aqicn.org/data-platform/token/
    waqi_base_url: str = "https://api.waqi.info"
    
    # Request timeout and retry settings
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5


@dataclass
class DataConfig:
    """Data collection and processing configuration"""
    # Cities to monitor (you can add more)
    cities: List[dict] = None
    
    # Data collection intervals
    collection_interval_seconds: int = 300  # 5 minutes
    batch_processing_interval_seconds: int = 1800  # 30 minutes
    
    # Data quality thresholds
    max_aqi_value: int = 500
    min_valid_readings_per_hour: int = 6
    
    # Alert thresholds
    aqi_alert_thresholds: dict = None
    
    def __post_init__(self):
        if self.cities is None:
            self.cities = [
                {"name": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060},
                {"name": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278},
                {"name": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503},
                {"name": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.4074},
                {"name": "Delhi", "country": "India", "lat": 28.7041, "lon": 77.1025},
                {"name": "Los Angeles", "country": "USA", "lat": 34.0522, "lon": -118.2437},
                {"name": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332},
                {"name": "São Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333}
            ]
            
        if self.aqi_alert_thresholds is None:
            self.aqi_alert_thresholds = {
                "moderate": 51,      # AQI 51-100
                "unhealthy_sensitive": 101,  # AQI 101-150
                "unhealthy": 151,    # AQI 151-200
                "very_unhealthy": 201,  # AQI 201-300
                "hazardous": 301     # AQI 301+
            }


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    log_file: str = "/app/logs/air_quality.log"
    rotation: str = "1 day"
    retention: str = "30 days"


class Config:
    """Main configuration class that combines all configs"""
    
    def __init__(self):
        # Load environment variables
        self._load_from_env()
        
        # Initialize configuration sections
        self.kafka = KafkaConfig(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        )
        
        self.postgres = PostgresConfig(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "airquality"),
            username=os.getenv("POSTGRES_USER", "airquality_user"),
            password=os.getenv("POSTGRES_PASSWORD", "airquality_pass")
        )
        


        
        self.api = APIConfig(
            openweather_api_key=os.getenv("OPENWEATHER_API_KEY"),
            airvisual_api_key=os.getenv("AIRVISUAL_API_KEY"),
            waqi_api_key=os.getenv("WAQI_API_KEY")
        )
        
        self.data = DataConfig()
        self.logging = LoggingConfig()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Try to load .env file if it exists
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
    
    def get_api_key_instructions(self) -> str:
        """Return instructions for getting API keys"""
        return """
        To get API keys for air quality data:
        
        1. OpenWeatherMap (Free: 1000 calls/day):
           - Visit: https://openweathermap.org/api
           - Sign up for free account
           - Get API key from dashboard
           - Set environment variable: OPENWEATHER_API_KEY=your_key
        
        2. AirVisual (Free: 10000 calls/month):
           - Visit: https://www.iqair.com/air-pollution-data-api
           - Register for free account
           - Get API key
           - Set environment variable: AIRVISUAL_API_KEY=your_key
        
        3. World Air Quality Index (Free):
           - Visit: https://aqicn.org/data-platform/token/
           - Register and get token
           - Set environment variable: WAQI_API_KEY=your_key
        
        Note: The system will work with mock data if no API keys are provided.
        """
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        errors = []
        
        # Check if at least one API key is provided
        if not any([
            self.api.openweather_api_key,
            self.api.airvisual_api_key,
            self.api.waqi_api_key
        ]):
            errors.append("No API keys provided. System will use mock data.")
        
        # Validate data collection interval
        if self.data.collection_interval_seconds < 60:
            errors.append("Collection interval should be at least 60 seconds to avoid API rate limits")
        
        if errors:
            print("Configuration warnings:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True


# Global configuration instance
config = Config() 