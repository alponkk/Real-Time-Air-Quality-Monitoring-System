"""
Kafka Consumer for Air Quality Data
This consumes air quality data from Kafka topics and writes to PostgreSQL
"""

import json
import time
import psycopg2
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from loguru import logger
from datetime import datetime

class AirQualityKafkaConsumer:
    """Kafka consumer for air quality data"""
    
    def __init__(self):
        self.consumer = None
        self.postgres_conn = None
        self.setup_consumer()
        self.setup_postgres()
    
    def setup_consumer(self):
        """Setup Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                'air-quality-data',
                'air-quality-alerts',
                bootstrap_servers=['kafka:29092'],
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='air-quality-consumer-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None,
                consumer_timeout_ms=-1,  # No timeout - keep running continuously
                session_timeout_ms=30000,  # 30 second session timeout
                heartbeat_interval_ms=10000,  # 10 second heartbeat
                api_version=(0, 10, 2)
            )
            logger.info("✅ Kafka consumer connected successfully")
            logger.info(f"📋 Subscribed to topics: {self.consumer.subscription()}")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup Kafka consumer: {str(e)}")
            raise
    
    def setup_postgres(self):
        """Setup PostgreSQL connection"""
        try:
            self.postgres_conn = psycopg2.connect(
                host="postgres",
                database="airquality",
                user="airquality_user",
                password="airquality_pass"
            )
            logger.info("✅ PostgreSQL connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {str(e)}")
            raise
    
    def process_air_quality_message(self, message):
        """Process air quality measurement message"""
        try:
            data = message.value
            
            # Skip if not air quality measurement
            if data.get('message_type') != 'air_quality_measurement':
                return
            
            # Insert into PostgreSQL
            cursor = self.postgres_conn.cursor()
            
            insert_sql = """
            INSERT INTO air_quality_measurements (
                city, country, latitude, longitude, timestamp,
                aqi, aqi_category, pm25, pm10, no2, so2, co, o3,
                temperature, humidity, pressure, wind_speed, wind_direction,
                data_source, data_quality
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT DO NOTHING
            """
            
            cursor.execute(insert_sql, (
                data['city'], data['country'], data['latitude'], data['longitude'],
                data['timestamp'], data['aqi'], data['aqi_category'],
                data.get('pm25'), data.get('pm10'), data.get('no2'), data.get('so2'), 
                data.get('co'), data.get('o3'), data.get('temperature'), data.get('humidity'),
                data.get('pressure'), data.get('wind_speed'), data.get('wind_direction'),
                data['data_source'], data['data_quality']
            ))
            
            self.postgres_conn.commit()
            cursor.close()
            
            logger.info(f"📊 Processed: {data['city']} - AQI: {data['aqi']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing air quality message: {str(e)}")
            return False
    
    def process_alert_message(self, message):
        """Process alert message"""
        try:
            data = message.value
            
            # Skip if not alert
            if data.get('message_type') != 'air_quality_alert':
                return
            
            # Insert into alerts table
            cursor = self.postgres_conn.cursor()
            
            insert_sql = """
            INSERT INTO air_quality_alerts (
                city, country, alert_type, alert_level, message,
                aqi_value, threshold_exceeded, timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """
            
            cursor.execute(insert_sql, (
                data['city'], data['country'], data['alert_type'], 
                data['alert_level'], data['message'], data['aqi_value'],
                data['threshold_exceeded'], data['timestamp']
            ))
            
            self.postgres_conn.commit()
            cursor.close()
            
            logger.warning(f"🚨 Alert processed: {data['city']} - {data['message']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing alert message: {str(e)}")
            return False
    
    def start_consuming(self):
        """Start consuming messages from Kafka"""
        logger.info("🚀 Starting Kafka consumer...")
        
        try:
            processed_count = 0
            
            for message in self.consumer:
                try:
                    logger.debug(f"📨 Received message from topic: {message.topic}")
                    
                    if message.topic == 'air-quality-data':
                        if self.process_air_quality_message(message):
                            processed_count += 1
                            
                    elif message.topic == 'air-quality-alerts':
                        if self.process_alert_message(message):
                            processed_count += 1
                    
                    # Log progress every 10 messages
                    if processed_count % 10 == 0 and processed_count > 0:
                        logger.info(f"📈 Total messages processed: {processed_count}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing message: {str(e)}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("⏹️ Consumer stopped by user")
        except Exception as e:
            logger.error(f"❌ Consumer error: {str(e)}")
        finally:
            self.close()
    
    def close(self):
        """Close connections"""
        if self.consumer:
            self.consumer.close()
            logger.info("🔌 Kafka consumer closed")
            
        if self.postgres_conn:
            self.postgres_conn.close()
            logger.info("🔌 PostgreSQL connection closed")

def main():
    """Run the consumer"""
    consumer = AirQualityKafkaConsumer()
    consumer.start_consuming()

if __name__ == "__main__":
    main() 