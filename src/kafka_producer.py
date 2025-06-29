"""
Kafka Producer for Air Quality Data

This module handles publishing air quality data and alerts to Kafka topics.
"""

import json
import time
from typing import Dict, List, Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError
from loguru import logger

from config import config


class AirQualityKafkaProducer:
    """Kafka producer for air quality data and alerts"""
    
    def __init__(self):
        self.config = config
        self.producer = None
        self.connect()
    
    def connect(self):
        """Connect to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.kafka.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                batch_size=16384,
                linger_ms=10,  # Wait up to 10ms to batch messages
                buffer_memory=33554432,  # 32MB buffer
                compression_type='gzip',
                max_request_size=1048576,  # 1MB max message size
                retry_backoff_ms=100,
                api_version=(0, 10, 2)
            )
            logger.info("Connected to Kafka broker successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {str(e)}")
            self.producer = None
            raise

    def publish_air_quality_data(self, data: Dict) -> bool:
        """Publish air quality data to Kafka topic"""
        if not self.producer:
            logger.error("Kafka producer is not connected")
            return False
        
        try:
            # Use city name as the key for partitioning
            key = f"{data.get('city', 'unknown')}_{data.get('country', 'unknown')}"
            
            # Add metadata
            message = {
                **data,
                'message_type': 'air_quality_measurement',
                'published_at': time.time()
            }
            
            future = self.producer.send(
                topic=self.config.kafka.air_quality_topic,
                key=key,
                value=message
            )
            
            # Wait for the message to be sent (optional, for reliability)
            result = future.get(timeout=10)
            
            logger.debug(f"Published air quality data for {key} to partition {result.partition}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to publish air quality data: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing air quality data: {str(e)}")
            return False

    def publish_alert(self, alert: Dict) -> bool:
        """Publish air quality alert to Kafka topic"""
        if not self.producer:
            logger.error("Kafka producer is not connected")
            return False
        
        try:
            # Use city name as the key for partitioning
            key = f"{alert.get('city', 'unknown')}_{alert.get('country', 'unknown')}"
            
            # Add metadata
            message = {
                **alert,
                'message_type': 'air_quality_alert',
                'published_at': time.time()
            }
            
            future = self.producer.send(
                topic=self.config.kafka.alerts_topic,
                key=key,
                value=message
            )
            
            # Wait for the message to be sent
            result = future.get(timeout=10)
            
            logger.info(f"Published alert for {key}: {alert.get('alert_type', 'unknown')}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to publish alert: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing alert: {str(e)}")
            return False

    def publish_batch_data(self, data_list: List[Dict]) -> int:
        """Publish multiple air quality measurements in batch"""
        if not self.producer:
            logger.error("Kafka producer is not connected")
            return 0
        
        success_count = 0
        
        for data in data_list:
            if self.publish_air_quality_data(data):
                success_count += 1
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        
        logger.info(f"Published {success_count}/{len(data_list)} air quality measurements")
        return success_count

    def create_topics_if_not_exist(self):
        """Create Kafka topics if they don't exist"""
        try:
            from kafka.admin import KafkaAdminClient, NewTopic
            from kafka.errors import TopicAlreadyExistsError
            
            admin_client = KafkaAdminClient(
                bootstrap_servers=self.config.kafka.bootstrap_servers
            )
            
            topics = [
                NewTopic(
                    name=self.config.kafka.air_quality_topic,
                    num_partitions=3,
                    replication_factor=1
                ),
                NewTopic(
                    name=self.config.kafka.alerts_topic,
                    num_partitions=3,
                    replication_factor=1
                )
            ]
            
            try:
                admin_client.create_topics(topics)
                logger.info("Created Kafka topics successfully")
            except TopicAlreadyExistsError:
                logger.info("Kafka topics already exist")
                
        except Exception as e:
            logger.warning(f"Could not create topics: {str(e)}")

    def get_topic_metadata(self) -> Dict:
        """Get metadata about Kafka topics"""
        if not self.producer:
            return {}
        
        try:
            metadata = self.producer._metadata
            topics_info = {}
            
            for topic in [self.config.kafka.air_quality_topic, self.config.kafka.alerts_topic]:
                if topic in metadata.topics:
                    topic_metadata = metadata.topics[topic]
                    topics_info[topic] = {
                        'partitions': len(topic_metadata.partitions),
                        'available': len([p for p in topic_metadata.partitions.values() if p.leader >= 0])
                    }
                else:
                    topics_info[topic] = {'partitions': 0, 'available': 0}
            
            return topics_info
            
        except Exception as e:
            logger.error(f"Error getting topic metadata: {str(e)}")
            return {}

    def health_check(self) -> bool:
        """Check if Kafka producer is healthy"""
        try:
            if not self.producer:
                return False
            
            # Try to get metadata (this will fail if connection is broken)
            self.producer._metadata.topics
            return True
            
        except Exception:
            return False

    def close(self):
        """Close the Kafka producer"""
        if self.producer:
            try:
                self.producer.flush(timeout=30)  # Wait up to 30 seconds for pending messages
                self.producer.close(timeout=30)
                logger.info("Kafka producer closed successfully")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {str(e)}")
            finally:
                self.producer = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class MockKafkaProducer:
    """Mock Kafka producer for testing without Kafka"""
    
    def __init__(self):
        self.messages = []
        logger.info("Using mock Kafka producer")
    
    def publish_air_quality_data(self, data: Dict) -> bool:
        self.messages.append(('air_quality', data))
        logger.debug(f"Mock: Published air quality data for {data.get('city', 'unknown')}")
        return True
    
    def publish_alert(self, alert: Dict) -> bool:
        self.messages.append(('alert', alert))
        logger.info(f"Mock: Published alert for {alert.get('city', 'unknown')}")
        return True
    
    def publish_batch_data(self, data_list: List[Dict]) -> int:
        for data in data_list:
            self.publish_air_quality_data(data)
        return len(data_list)
    
    def create_topics_if_not_exist(self):
        logger.info("Mock: Topics created")
    
    def get_topic_metadata(self) -> Dict:
        return {
            'air-quality-data': {'partitions': 3, 'available': 3},
            'air-quality-alerts': {'partitions': 3, 'available': 3}
        }
    
    def health_check(self) -> bool:
        return True
    
    def close(self):
        logger.info(f"Mock producer closed. Published {len(self.messages)} messages total")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def create_producer(use_mock: bool = False) -> AirQualityKafkaProducer:
    """Factory function to create Kafka producer"""
    if use_mock:
        return MockKafkaProducer()
    else:
        return AirQualityKafkaProducer() 