"""Test sensor API endpoints."""
import pytest
from httpx import AsyncClient
from datetime import datetime


class TestSensorAPI:
    """Test sensor data endpoints."""
    
    async def test_create_sensor_data(self, client: AsyncClient):
        """Test creating sensor data."""
        sensor_data = {
            "sensor_id": "sensor_001",
            "sensor_type": "temperature",
            "value": 23.5,
            "unit": "celsius",
            "location": "building_a_floor_1"
        }
        
        response = await client.post("/api/v1/sensors/data", json=sensor_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["sensor_id"] == sensor_data["sensor_id"]
        assert data["sensor_type"] == sensor_data["sensor_type"]
        assert data["value"] == sensor_data["value"]
        assert data["unit"] == sensor_data["unit"]
        assert data["location"] == sensor_data["location"]
        assert "id" in data
        assert "timestamp" in data
    
    async def test_get_sensor_data(self, client: AsyncClient):
        """Test getting sensor data."""
        # First create some test data
        sensor_data = {
            "sensor_id": "sensor_002",
            "sensor_type": "humidity",
            "value": 65.0,
            "unit": "percent",
            "location": "building_a_floor_2"
        }
        
        await client.post("/api/v1/sensors/data", json=sensor_data)
        
        # Get all sensor data
        response = await client.get("/api/v1/sensors/data")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    async def test_get_sensor_data_with_filter(self, client: AsyncClient):
        """Test getting sensor data with filters."""
        # Create test data
        sensor_data = {
            "sensor_id": "sensor_003",
            "sensor_type": "pressure",
            "value": 1013.25,
            "unit": "hPa",
            "location": "building_b"
        }
        
        await client.post("/api/v1/sensors/data", json=sensor_data)
        
        # Get data filtered by sensor_id
        response = await client.get(
            "/api/v1/sensors/data",
            params={"sensor_id": "sensor_003"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        assert all(item["sensor_id"] == "sensor_003" for item in data)
    
    async def test_get_latest_sensor_data(self, client: AsyncClient):
        """Test getting latest sensor data for a specific sensor."""
        # Create test data
        sensor_data = {
            "sensor_id": "sensor_004",
            "sensor_type": "vibration",
            "value": 0.5,
            "unit": "mm/s",
            "location": "track_section_1"
        }
        
        await client.post("/api/v1/sensors/data", json=sensor_data)
        
        # Get latest data
        response = await client.get("/api/v1/sensors/data/sensor_004/latest")
        assert response.status_code == 200
        
        data = response.json()
        assert data["sensor_id"] == "sensor_004"
        assert data["sensor_type"] == "vibration"
        assert data["value"] == 0.5
    
    async def test_get_latest_sensor_data_not_found(self, client: AsyncClient):
        """Test getting latest sensor data for non-existent sensor."""
        response = await client.get("/api/v1/sensors/data/nonexistent/latest")
        assert response.status_code == 404
    
    async def test_get_anomaly_alerts(self, client: AsyncClient):
        """Test getting anomaly alerts."""
        response = await client.get("/api/v1/sensors/alerts")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    async def test_create_sensor_data_validation(self, client: AsyncClient):
        """Test sensor data validation."""
        # Test missing required fields
        invalid_data = {
            "sensor_id": "sensor_005",
            # Missing sensor_type, value, unit
        }
        
        response = await client.post("/api/v1/sensors/data", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    async def test_sensor_data_limits(self, client: AsyncClient):
        """Test sensor data pagination limits."""
        response = await client.get(
            "/api/v1/sensors/data",
            params={"limit": 5, "offset": 0}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) <= 5