# Device Service

The Device Service is the core microservice responsible for device communication, real-time monitoring, and command execution in the Nattery battery energy trading system.

## 🎯 Purpose

The Device Service acts as the primary interface between the Edge Bridge hardware layer and the rest of the microservices architecture. It processes real-time device data, manages device states, executes commands, and provides WebSocket connections for live updates.

## 🏗️ Architecture

```
Edge Bridge (MQTT) ← Device Service → Frontend (WebSocket)
                   ↓
              [PostgreSQL + InfluxDB + Redis]
                   ↓
              Other Services (RabbitMQ)
```

### Key Components

- **MQTT Manager**: Subscribes to Edge Bridge topics for device data, status, and alerts
- **Database Manager**: Handles PostgreSQL (metadata) and InfluxDB (time-series) operations
- **Device Manager**: Manages device registration, status updates, and configuration
- **Data Processor**: Processes and enriches incoming device data
- **Command Manager**: Handles command queuing, execution, and status tracking
- **WebSocket Manager**: Provides real-time updates to connected clients
- **Health Monitor**: Monitors service and component health

## 📊 Data Flow

### Incoming Data (from Edge Bridge via MQTT)
1. **Device Data**: Real-time metrics (battery voltage, current, power, etc.)
2. **Device Status**: Connection status, health, and operational state
3. **Device Alerts**: Warnings, errors, and critical notifications
4. **Command Responses**: Results from executed commands

### Outgoing Data
1. **WebSocket Events**: Real-time updates to frontend clients
2. **RabbitMQ Messages**: Inter-service communication
3. **Database Storage**: Persistent storage of device data and metadata

## 🔌 API Endpoints

### Health Endpoints
- `GET /health` - Basic health check
- `GET /api/health` - Detailed health status
- `GET /api/health/detailed` - Comprehensive health report

### Device Management
- `GET /api/devices` - List all devices
- `GET /api/devices/:deviceId` - Get device details
- `POST /api/devices` - Register new device
- `PUT /api/devices/:deviceId` - Update device configuration
- `DELETE /api/devices/:deviceId` - Remove device

### Device Data
- `GET /api/data/:deviceId` - Get latest device data
- `GET /api/data/:deviceId/history` - Get historical data
- `GET /api/data/:deviceId/metrics` - Get device metrics summary

### Command Management
- `POST /api/commands` - Execute device command
- `GET /api/commands/:commandId` - Get command status
- `GET /api/commands/device/:deviceId` - Get device command history
- `DELETE /api/commands/:commandId` - Cancel pending command

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Service port | `3001` |
| `NODE_ENV` | Environment | `development` |
| `DATABASE_URL` | PostgreSQL connection | Required |
| `INFLUXDB_URL` | InfluxDB connection | Required |
| `INFLUXDB_TOKEN` | InfluxDB authentication | Required |
| `REDIS_URL` | Redis connection | Required |
| `MQTT_BROKER_URL` | MQTT broker URL | Required |
| `MQTT_USERNAME` | MQTT authentication | Optional |
| `MQTT_PASSWORD` | MQTT authentication | Optional |
| `RABBITMQ_URL` | RabbitMQ connection | Required |

### MQTT Topics

The service subscribes to these MQTT topics from the Edge Bridge:

- `nattery/+/data` - Device data updates
- `nattery/+/status` - Device status changes
- `nattery/+/alerts` - Device alerts and notifications
- `nattery/+/commands/response` - Command execution responses

## 🗄️ Database Schema

### PostgreSQL Tables

- **devices** - Device registration and metadata
- **device_commands** - Command history and status
- **device_events** - Device events and state changes
- **device_alerts** - Alert management and tracking
- **device_configs** - Device-specific configuration
- **device_metrics** - Latest device metrics summary

### InfluxDB Measurements

- **device_data** - Time-series device metrics
- **device_performance** - Calculated performance metrics
- **device_energy** - Energy flow and consumption data

## 🚀 Development

### Prerequisites

- Node.js 18+
- PostgreSQL 15+
- InfluxDB 2.7+
- Redis 7+
- MQTT Broker (Mosquitto)

### Setup

```bash
# Install dependencies
yarn install

# Generate Prisma client
yarn prisma generate

# Run database migrations
yarn prisma migrate dev

# Start development server
yarn dev
```

### Testing

```bash
# Run unit tests
yarn test

# Run tests in watch mode
yarn test:watch

# Test service connectivity
make device-service-test
```

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t nattery/device-service .
```

### Run Container

```bash
docker run -d \
  --name nattery-device-service \
  -p 3001:3001 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e INFLUXDB_URL="http://influxdb:8086" \
  -e INFLUXDB_TOKEN="your-token" \
  -e REDIS_URL="redis://redis:6379" \
  -e MQTT_BROKER_URL="mqtt://mosquitto:1883" \
  nattery/device-service
```

### Docker Compose

```bash
# Start all services
make docker-up

# View logs
make device-service-logs

# Access container shell
make device-service-shell
```

## 📡 WebSocket Events

The service provides real-time updates via WebSocket connections:

### Client Events (Incoming)
- `join_device` - Subscribe to device updates
- `leave_device` - Unsubscribe from device updates
- `get_device_status` - Request current device status

### Server Events (Outgoing)
- `device_data` - Real-time device data updates
- `device_status` - Device status changes
- `device_alert` - Device alerts and notifications
- `command_response` - Command execution results

### Example Usage

```javascript
const socket = io('http://localhost:3001');

// Subscribe to device updates
socket.emit('join_device', { deviceId: 'inverter-001' });

// Listen for real-time data
socket.on('device_data', (data) => {
  console.log('Device data:', data);
});

// Listen for alerts
socket.on('device_alert', (alert) => {
  console.log('Device alert:', alert);
});
```

## 🔍 Monitoring

### Health Checks

The service provides comprehensive health monitoring:

```bash
# Basic health check
curl http://localhost:3001/health

# Detailed health status
curl http://localhost:3001/api/health/detailed
```

### Metrics

Key performance indicators tracked:

- **Message Processing Rate**: MQTT messages per second
- **Database Performance**: Query latency and throughput
- **WebSocket Connections**: Active connections and events
- **Command Execution**: Success rate and response times
- **Error Rates**: Service and component error frequencies

### Logging

Structured logging with Winston:

- **Development**: Console output with colors
- **Production**: JSON format with file rotation
- **Log Levels**: error, warn, info, debug

## 🔒 Security

### Authentication

- JWT token validation for API endpoints
- MQTT authentication with username/password
- Database connection encryption

### Authorization

- Role-based access control for device operations
- Device-specific permissions
- Command execution authorization

### Data Protection

- Sensitive configuration encryption
- Audit logging for all operations
- Rate limiting on API endpoints

## 🚨 Error Handling

### MQTT Connection Issues
- Automatic reconnection with exponential backoff
- Message queuing during disconnections
- Health status reporting

### Database Failures
- Connection pooling and retry logic
- Graceful degradation for read operations
- Transaction rollback on failures

### Command Execution Errors
- Timeout handling with configurable limits
- Retry logic with exponential backoff
- Error reporting and alerting

## 📈 Performance

### Optimization Strategies

- **Connection Pooling**: Database and Redis connections
- **Message Batching**: Bulk operations for high-throughput data
- **Caching**: Redis caching for frequently accessed data
- **Indexing**: Optimized database indexes for queries

### Scaling Considerations

- **Horizontal Scaling**: Multiple service instances
- **Load Balancing**: Distribute WebSocket connections
- **Database Sharding**: Partition data by device or time
- **Message Queuing**: RabbitMQ for inter-service communication

## 🔧 Troubleshooting

### Common Issues

1. **MQTT Connection Failed**
   - Check broker URL and credentials
   - Verify network connectivity
   - Review firewall settings

2. **Database Connection Error**
   - Validate connection string
   - Check database server status
   - Verify credentials and permissions

3. **High Memory Usage**
   - Monitor WebSocket connections
   - Check for memory leaks in data processing
   - Review caching strategies

4. **Slow Response Times**
   - Analyze database query performance
   - Check InfluxDB write performance
   - Monitor network latency

### Debug Commands

```bash
# View service logs
make device-service-logs

# Access container for debugging
make device-service-shell

# Check database migrations
make device-service-db-migrate

# Open Prisma Studio
make device-service-db-studio
```

## 📚 Related Documentation

- [Edge Bridge Service](../edge-bridge/README.md)
- [API Gateway Configuration](../../gateway/README.md)
- [Database Schema](./prisma/schema.prisma)
- [MQTT Topic Structure](../../docs/mqtt-topics.md)
- [WebSocket API](../../docs/websocket-api.md)

---

**Part of the Nattery Battery Energy Trading System** 