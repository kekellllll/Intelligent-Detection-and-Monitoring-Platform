"""Test monitoring endpoints."""
import pytest
from httpx import AsyncClient


class TestMonitoringAPI:
    """Test monitoring and health endpoints."""
    
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["platform"] == "intelligent-detection-monitoring"
    
    async def test_detailed_health_check(self, client: AsyncClient):
        """Test detailed health check endpoint."""
        response = await client.get("/api/v1/monitoring/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
    
    async def test_platform_stats(self, client: AsyncClient):
        """Test platform statistics endpoint."""
        response = await client.get("/api/v1/monitoring/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_data_points" in data
        assert "total_anomalies" in data
        assert "active_sensors" in data
        assert "platform_uptime_percent" in data
        assert "timestamp" in data
    
    async def test_sensors_status(self, client: AsyncClient):
        """Test sensors status endpoint."""
        response = await client.get("/api/v1/monitoring/sensors/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "sensors" in data
        assert "total_count" in data
        assert "healthy_count" in data
        assert "stale_count" in data
        assert isinstance(data["sensors"], list)