# Intelligent Detection and Monitoring Platform

A distributed system for intelligent sensor data monitoring and anomaly detection, built with Python and FastAPI. This platform provides real-time monitoring, machine learning-based anomaly detection, and high-throughput data processing capabilities.

## 🏗️ Architecture

### Core Technologies
- **FastAPI**: High-performance web framework for building APIs
- **Redis**: Message queuing and caching for real-time data processing
- **Kafka**: High-throughput distributed streaming platform
- **TensorFlow**: Machine learning framework for anomaly detection
- **PostgreSQL**: Primary database for sensor data storage
- **GraphQL**: Flexible API query language for complex data retrieval
- **Kubernetes**: Container orchestration for high availability deployment

### System Components
1. **API Layer**: RESTful and GraphQL APIs for data ingestion and querying
2. **Message Queue**: Redis for real-time processing and Kafka for batch processing
3. **ML Engine**: TensorFlow-based anomaly detection with 95% accuracy target
4. **Database**: PostgreSQL for persistent storage with async support
5. **Monitoring**: Prometheus metrics and health checks for 99.9% uptime

## 🚀 Features

### Data Processing Pipeline
- **Real-time ingestion**: Process sensor data as it arrives
- **Batch processing**: High-throughput analysis using Kafka and Spark Streaming
- **Intelligent caching**: Redis-based caching for frequently accessed data
- **Asynchronous processing**: Non-blocking operations for better performance

### Anomaly Detection
- **ML-powered detection**: TensorFlow models with LSTM architecture
- **95% accuracy**: Advanced time-series analysis for reliable detection
- **Multi-severity alerts**: Critical, high, medium, and low severity levels
- **Historical context**: 24-hour rolling window for better predictions

### API Capabilities
- **RESTful endpoints**: Standard HTTP APIs for CRUD operations
- **GraphQL interface**: Flexible queries for complex monitoring data
- **Real-time subscriptions**: WebSocket support for live updates
- **Comprehensive filtering**: Query by sensor type, location, time range

### Deployment & Reliability
- **Containerized**: Docker containers for consistent deployments
- **Kubernetes-ready**: Production-grade orchestration with health checks
- **High availability**: Multi-replica deployments with load balancing
- **Monitoring & alerting**: Prometheus metrics and structured logging

## 📋 Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Kubernetes cluster (for production deployment)
- PostgreSQL database
- Redis server
- Apache Kafka

## 🛠️ Installation

### Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/kekellllll/Intelligent-Detection-and-Monitoring-Platform.git
cd Intelligent-Detection-and-Monitoring-Platform
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start development services**
```bash
docker-compose up -d db redis kafka
```

6. **Run database migrations**
```bash
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

7. **Start the application**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Kubernetes Deployment

```bash
# Create namespace and deploy
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/kafka.yaml
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get pods -n monitoring-platform
```

## 📖 API Documentation

### REST API

The REST API is available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

**Key Endpoints:**
- `POST /api/v1/sensors/data` - Submit sensor data
- `GET /api/v1/sensors/data` - Retrieve sensor data with filtering
- `GET /api/v1/sensors/alerts` - Get anomaly alerts
- `GET /api/v1/monitoring/stats` - Platform statistics
- `GET /api/v1/monitoring/health` - Health check

### GraphQL API

GraphQL playground available at `/api/v1/graphql`

**Example Queries:**
```graphql
# Get sensor data with filtering
query {
  sensorData(sensorId: "sensor_001", limit: 10) {
    id
    sensorId
    value
    timestamp
    isAnomaly
    anomalyScore
  }
}

# Get anomaly alerts
query {
  anomalyAlerts(severity: "high", resolved: false) {
    id
    sensorId
    severity
    message
    timestamp
  }
}
```

### Sensor Data Format

```json
{
  "sensor_id": "sensor_001",
  "sensor_type": "temperature",
  "value": 23.5,
  "unit": "celsius",
  "location": "building_a_floor_1",
  "metadata": {
    "building": "A",
    "floor": 1,
    "room": "server_room"
  }
}
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_sensors.py -v
```

### Load Testing
```bash
# Install testing tools
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8000
```

## 📊 Monitoring

### Metrics

Prometheus metrics available at `/api/v1/monitoring/metrics`:
- `sensor_data_total`: Total sensor data received
- `anomalies_detected_total`: Total anomalies detected
- `data_processing_seconds`: Processing time histogram
- `active_sensors_count`: Number of active sensors

### Health Checks

- **Basic**: `GET /health`
- **Detailed**: `GET /api/v1/monitoring/health`
- **Statistics**: `GET /api/v1/monitoring/stats`

### Logging

Structured logging with configurable levels:
```bash
# Set log level
export LOG_LEVEL=DEBUG
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | `localhost:9092` |
| `MODEL_ACCURACY_THRESHOLD` | ML model threshold | `0.95` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Model Configuration

The anomaly detection model can be configured via:
- `MODEL_PATH`: Path to trained model file
- `MODEL_ACCURACY_THRESHOLD`: Minimum confidence threshold
- Feature engineering parameters in `app/ml/anomaly_detection.py`

## 🎯 Performance Targets

- **Uptime**: 99.9% platform availability
- **Accuracy**: 95% anomaly detection accuracy
- **Throughput**: Handle high-volume sensor data streams
- **Latency**: Sub-second response times for API requests
- **Scalability**: Horizontal scaling with Kubernetes

## 🔐 Security

- **Authentication**: Token-based authentication (implement as needed)
- **Data validation**: Pydantic models for input validation
- **SQL injection protection**: SQLAlchemy ORM with parameterized queries
- **CORS**: Configurable cross-origin resource sharing
- **Secrets management**: Kubernetes secrets for sensitive data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation as needed
- Use type hints throughout the codebase

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Review the API documentation at `/docs`
- Check the monitoring endpoints for system health

## 🗺️ Roadmap

### Phase 1: Core Platform ✅
- [x] FastAPI application with microservices architecture
- [x] Redis integration for message queuing
- [x] Docker containerization
- [x] Basic API endpoints

### Phase 2: Data Processing ✅
- [x] Kafka integration for high-throughput streaming
- [x] Database models and storage
- [x] Async data processing pipeline

### Phase 3: ML & Analytics ✅
- [x] TensorFlow-based anomaly detection
- [x] Model training and inference pipeline
- [x] Alert generation system

### Phase 4: Production Ready ✅
- [x] Kubernetes deployment configurations
- [x] Monitoring and health checks
- [x] GraphQL API implementation
- [x] Comprehensive testing

### Phase 5: Future Enhancements
- [ ] Advanced ML models (AutoML, ensemble methods)
- [ ] Real-time dashboards and visualization
- [ ] Mobile app for alerts and monitoring
- [ ] Integration with external monitoring systems
- [ ] Advanced analytics and reporting