-- Air Quality Database Initialization Script

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Air Quality Measurements Table
CREATE TABLE IF NOT EXISTS air_quality_measurements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Air Quality Index
    aqi INTEGER,
    aqi_category VARCHAR(50),
    
    -- Pollutant measurements (μg/m³)
    pm25 DECIMAL(8, 3),          -- PM2.5
    pm10 DECIMAL(8, 3),          -- PM10
    no2 DECIMAL(8, 3),           -- Nitrogen Dioxide
    so2 DECIMAL(8, 3),           -- Sulfur Dioxide
    co DECIMAL(8, 3),            -- Carbon Monoxide
    o3 DECIMAL(8, 3),            -- Ozone
    
    -- Weather data
    temperature DECIMAL(5, 2),   -- Celsius
    humidity DECIMAL(5, 2),      -- Percentage
    pressure DECIMAL(7, 2),      -- hPa
    wind_speed DECIMAL(5, 2),    -- m/s
    wind_direction INTEGER,      -- degrees
    
    -- Data source and quality
    data_source VARCHAR(100),
    data_quality VARCHAR(20),
    
    -- Indexing for time-series queries
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_air_quality_timestamp ON air_quality_measurements(timestamp);
CREATE INDEX IF NOT EXISTS idx_air_quality_city ON air_quality_measurements(city);
CREATE INDEX IF NOT EXISTS idx_air_quality_country ON air_quality_measurements(country);
CREATE INDEX IF NOT EXISTS idx_air_quality_aqi ON air_quality_measurements(aqi);
CREATE INDEX IF NOT EXISTS idx_air_quality_created_at ON air_quality_measurements(created_at);

-- Air Quality Stations Table (for reference data)
CREATE TABLE IF NOT EXISTS air_quality_stations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    station_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    elevation INTEGER,           -- meters above sea level
    station_type VARCHAR(50),    -- urban, suburban, rural, industrial
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Air Quality Alerts Table
CREATE TABLE IF NOT EXISTS air_quality_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,  -- high_aqi, unhealthy, hazardous
    alert_level VARCHAR(20) NOT NULL, -- warning, danger, emergency
    message TEXT,
    aqi_value INTEGER,
    threshold_exceeded VARCHAR(50),   -- pm25, pm10, no2, etc.
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Daily Air Quality Summary Table (for aggregated data)
CREATE TABLE IF NOT EXISTS daily_air_quality_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    
    -- Average values for the day
    avg_aqi DECIMAL(5, 2),
    max_aqi INTEGER,
    min_aqi INTEGER,
    avg_pm25 DECIMAL(8, 3),
    max_pm25 DECIMAL(8, 3),
    avg_pm10 DECIMAL(8, 3),
    max_pm10 DECIMAL(8, 3),
    avg_no2 DECIMAL(8, 3),
    avg_so2 DECIMAL(8, 3),
    avg_co DECIMAL(8, 3),
    avg_o3 DECIMAL(8, 3),
    
    -- Weather summary
    avg_temperature DECIMAL(5, 2),
    max_temperature DECIMAL(5, 2),
    min_temperature DECIMAL(5, 2),
    avg_humidity DECIMAL(5, 2),
    avg_pressure DECIMAL(7, 2),
    avg_wind_speed DECIMAL(5, 2),
    
    -- Data quality metrics
    total_measurements INTEGER DEFAULT 0,
    valid_measurements INTEGER DEFAULT 0,
    data_completeness DECIMAL(5, 2), -- percentage
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicates
    UNIQUE(city, country, date)
);

-- Create indexes for summary table
CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON daily_air_quality_summary(date);
CREATE INDEX IF NOT EXISTS idx_daily_summary_city_date ON daily_air_quality_summary(city, date);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_air_quality_measurements_updated_at
    BEFORE UPDATE ON air_quality_measurements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample stations
INSERT INTO air_quality_stations (station_id, name, city, country, latitude, longitude, station_type) VALUES
('NYC_001', 'Manhattan Central Station', 'New York', 'USA', 40.7128, -74.0060, 'urban'),
('LON_001', 'London Central Station', 'London', 'UK', 51.5074, -0.1278, 'urban'),
('TKY_001', 'Tokyo Central Station', 'Tokyo', 'Japan', 35.6762, 139.6503, 'urban'),
('BEJ_001', 'Beijing Central Station', 'Beijing', 'China', 39.9042, 116.4074, 'urban'),
('DEL_001', 'Delhi Central Station', 'Delhi', 'India', 28.7041, 77.1025, 'urban')
ON CONFLICT (station_id) DO NOTHING;

-- Create a view for current air quality status
CREATE OR REPLACE VIEW current_air_quality_status AS
SELECT 
    city,
    country,
    latitude,
    longitude,
    aqi,
    aqi_category,
    pm25,
    pm10,
    no2,
    temperature,
    humidity,
    timestamp,
    data_source,
    ROW_NUMBER() OVER (PARTITION BY city, country ORDER BY timestamp DESC) as rn
FROM air_quality_measurements
WHERE timestamp >= NOW() - INTERVAL '24 hours';

-- Create a view for latest measurements per city
CREATE OR REPLACE VIEW latest_air_quality AS
SELECT 
    city,
    country,
    latitude,
    longitude,
    aqi,
    aqi_category,
    pm25,
    pm10,
    no2,
    so2,
    co,
    o3,
    temperature,
    humidity,
    pressure,
    wind_speed,
    wind_direction,
    timestamp,
    data_source,
    data_quality
FROM current_air_quality_status
WHERE rn = 1;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO airquality_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO airquality_user; 