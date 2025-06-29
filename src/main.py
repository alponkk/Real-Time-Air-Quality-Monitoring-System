"""
Main Application for Air Quality Monitoring System

This is the main entry point that orchestrates data collection,
Kafka publishing, and system monitoring.
"""

import asyncio
import signal
import sys
import time
from datetime import datetime
from threading import Thread, Event
from typing import Optional

import schedule
from loguru import logger

from config import config
from data_collector import AirQualityDataCollector
from kafka_producer import create_producer
from kafka_consumer import AirQualityKafkaConsumer


class AirQualityMonitoringSystem:
    """Main system orchestrator for air quality monitoring"""
    
    def __init__(self):
        self.config = config
        self.collector = AirQualityDataCollector()
        self.producer = None
        self.kafka_consumer = None
        self.running = Event()
        self.shutdown_event = Event()
        
        # Setup logging
        self._setup_logging()
        
        # System state
        self.last_collection_time = None
        self.total_measurements = 0
        self.total_alerts = 0
        self.errors_count = 0
        
    def _setup_logging(self):
        """Setup logging configuration"""
        # Remove default handler
        logger.remove()
        
        # Add console handler
        logger.add(
            sys.stderr,
            format=self.config.logging.format,
            level=self.config.logging.level,
            colorize=True
        )
        
        # Add file handler
        logger.add(
            self.config.logging.log_file,
            format=self.config.logging.format,
            level=self.config.logging.level,
            rotation=self.config.logging.rotation,
            retention=self.config.logging.retention,
            compression="zip"
        )

    def initialize(self) -> bool:
        """Initialize the monitoring system"""
        try:
            logger.info("Initializing Air Quality Monitoring System...")
            
            # Validate configuration
            if not self.config.validate():
                logger.warning("Configuration validation failed, continuing with warnings")
            
            # Initialize Kafka producer
            try:
                self.producer = create_producer(use_mock=False)
                self.producer.create_topics_if_not_exist()
                logger.info("Kafka producer initialized successfully")
            except Exception as e:
                logger.warning(f"Kafka producer failed, using mock: {str(e)}")
                self.producer = create_producer(use_mock=True)
            
            # Initialize Kafka consumer
            try:
                self.kafka_consumer = AirQualityKafkaConsumer()
                logger.info("Kafka consumer initialized successfully")
            except Exception as e:
                logger.warning(f"Kafka consumer initialization failed: {str(e)}")
                self.kafka_consumer = None
            
            # Print API instructions if no keys are provided
            if not any([
                self.config.api.openweather_api_key,
                self.config.api.airvisual_api_key,
                self.config.api.waqi_api_key
            ]):
                logger.info("No API keys detected. System will use mock data.")
                logger.info(self.config.get_api_key_instructions())
            
            # Setup scheduled tasks
            self._setup_schedule()
            
            logger.info("System initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {str(e)}")
            return False

    def _setup_schedule(self):
        """Setup scheduled data collection tasks"""
        # Schedule regular data collection
        schedule.every(self.config.data.collection_interval_seconds).seconds.do(
            self.collect_and_publish_data
        )
        
        # Schedule system health checks
        schedule.every(5).minutes.do(self.health_check)
        
        # Schedule daily summary reports
        schedule.every().day.at("00:00").do(self.generate_daily_summary)
        
        logger.info(f"Scheduled data collection every {self.config.data.collection_interval_seconds} seconds")

    def collect_and_publish_data(self):
        """Collect air quality data and publish to Kafka"""
        try:
            logger.info("Starting data collection cycle...")
            
            # Collect data for all cities
            start_time = time.time()
            all_data = self.collector.collect_all_cities_data()
            collection_time = time.time() - start_time
            
            if not all_data:
                logger.warning("No data collected in this cycle")
                self.errors_count += 1
                return
            
            # Publish data to Kafka
            success_count = 0
            alert_count = 0
            
            for data in all_data:
                # Publish air quality data
                if self.producer.publish_air_quality_data(data):
                    success_count += 1
                    self.total_measurements += 1
                
                # Check for alerts and publish if needed
                alert = self.collector.check_alert_conditions(data)
                if alert:
                    if self.producer.publish_alert(alert):
                        alert_count += 1
                        self.total_alerts += 1
                        logger.warning(f"Alert: {alert['message']}")
            
            # Update system state
            self.last_collection_time = datetime.now()
            
            # Log collection summary
            logger.info(
                f"Collection cycle completed: "
                f"{success_count}/{len(all_data)} measurements published, "
                f"{alert_count} alerts generated, "
                f"took {collection_time:.2f}s"
            )
            
            # Log API usage stats
            api_stats = self.collector.get_api_usage_stats()
            if api_stats['total_calls'] > 0:
                logger.debug(f"API usage: {api_stats}")
            
        except Exception as e:
            logger.error(f"Error in data collection cycle: {str(e)}")
            self.errors_count += 1

    def health_check(self):
        """Perform system health checks"""
        try:
            logger.info("Performing system health check...")
            
            # Check Kafka producer health
            kafka_healthy = self.producer.health_check() if self.producer else False
            
            # Check data collection freshness
            data_fresh = (
                self.last_collection_time is not None and
                (datetime.now() - self.last_collection_time).total_seconds() < 
                self.config.data.collection_interval_seconds * 2
            )
            
            # Log health status
            health_status = {
                'kafka_healthy': kafka_healthy,
                'data_fresh': data_fresh,
                'total_measurements': self.total_measurements,
                'total_alerts': self.total_alerts,
                'errors_count': self.errors_count,
                'last_collection': self.last_collection_time.isoformat() if self.last_collection_time else None
            }
            
            logger.info(f"Health check: {health_status}")
            
            # Generate alerts for system issues
            if not kafka_healthy:
                logger.error("Kafka producer is unhealthy!")
            
            if not data_fresh:
                logger.warning("Data collection appears stale!")
            
        except Exception as e:
            logger.error(f"Error during health check: {str(e)}")

    def generate_daily_summary(self):
        """Generate daily summary report"""
        try:
            logger.info("Generating daily summary report...")
            
            summary = {
                'date': datetime.now().date().isoformat(),
                'total_measurements': self.total_measurements,
                'total_alerts': self.total_alerts,
                'errors_count': self.errors_count,
                'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
            }
            
            logger.info(f"Daily summary: {summary}")
            
            # Reset daily counters
            self.total_measurements = 0
            self.total_alerts = 0
            self.errors_count = 0
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {str(e)}")

    def run_scheduler(self):
        """Run the scheduled tasks in a separate thread"""
        logger.info("Starting scheduler thread...")
        
        while self.running.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in scheduler: {str(e)}")
                time.sleep(5)
        
        logger.info("Scheduler thread stopped")

    def start(self):
        """Start the monitoring system"""
        if not self.initialize():
            logger.error("Failed to initialize system")
            return False
        
        try:
            self.start_time = datetime.now()
            self.running.set()
            
            logger.info("Starting Air Quality Monitoring System...")
            
            # Start scheduler in background thread
            scheduler_thread = Thread(target=self.run_scheduler, daemon=True)
            scheduler_thread.start()
            
            # Start Kafka consumer if available
            consumer_thread = None
            if self.kafka_consumer:
                try:
                    consumer_thread = Thread(target=self.kafka_consumer.start_consuming, daemon=True)
                    consumer_thread.start()
                    logger.info("Kafka consumer started in background")
                except Exception as e:
                    logger.warning(f"Failed to start Kafka consumer: {str(e)}")
            
            # Run initial data collection
            self.collect_and_publish_data()
            
            logger.info("System started successfully. Press Ctrl+C to stop.")
            
            # Keep main thread alive
            while self.running.is_set():
                try:
                    time.sleep(1)
                    
                    # Check if shutdown was requested
                    if self.shutdown_event.is_set():
                        break
                        
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received")
                    break
            
            return True
            
        except Exception as e:
            logger.error(f"Error running system: {str(e)}")
            return False
        finally:
            self.stop()

    def stop(self):
        """Stop the monitoring system gracefully"""
        logger.info("Stopping Air Quality Monitoring System...")
        
        # Signal threads to stop
        self.running.clear()
        
        # Close Kafka producer
        if self.producer:
            self.producer.close()
        
        # Stop Kafka consumer
        if self.kafka_consumer:
            try:
                self.kafka_consumer.close()
                logger.info("Kafka consumer stopped")
            except Exception as e:
                logger.warning(f"Error stopping Kafka consumer: {str(e)}")
        
        # Clear scheduled jobs
        schedule.clear()
        
        logger.info("System stopped gracefully")

    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}")
        self.shutdown_event.set()


def main():
    """Main entry point"""
    # Create system instance
    system = AirQualityMonitoringSystem()
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, system.signal_handler)
    signal.signal(signal.SIGTERM, system.signal_handler)
    
    try:
        # Start the system
        success = system.start()
        exit_code = 0 if success else 1
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main() 