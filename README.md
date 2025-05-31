# Nattery - Battery Energy Trading System

[![GitHub](https://img.shields.io/badge/GitHub-x--2b%2Fnattery--battery--trading-blue?logo=github)](https://github.com/x-2b/nattery-battery-trading)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://docs.docker.com/compose/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue?logo=typescript)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org/)

A scalable, microservices-based system for controlling and monitoring house batteries to enable energy trading through peak shaving and arbitrage strategies.

## 🏗️ Architecture Overview

Nattery implements a distributed architecture designed for reliability, scalability, and real-time performance:

```
Battery ← Inverter (Firmware) ← Modbus RTU ← USB Converter ← Raspberry Pi ← MQTT ← Microservices ← Web App
```

### Key Components

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS + Shadcn/ui
- **API Gateway**: Nginx with SSL termination, load balancing, and rate limiting
- **Microservices**: Device, Trading, Analytics, User, and Edge Bridge services
- **Message Brokers**: MQTT (IoT), RabbitMQ (services), Redis (caching)
- **Databases**: PostgreSQL (transactional), InfluxDB (time-series)
- **Edge Computing**: Python-based Modbus-MQTT bridge on Raspberry Pi

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and **Yarn** 1.22+
- **Docker** and **Docker Compose**
- **Make** (optional, for convenience commands)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/x-2b/nattery-battery-trading.git
   cd nattery-battery-trading
   ```

2. **Setup environment**
   ```bash
   make env          # Copy env.example to .env
   make setup        # Install dependencies and build types
   ```

3. **Start development environment**
   ```bash
   make dev          # Start all services in development mode
   # OR
   make docker-up    # Start with Docker Compose
   ```

4. **Access the application**
   - **Web Interface**: https://localhost (with SSL)
   - **API Gateway**: https://localhost/api/
   - **RabbitMQ Management**: http://localhost:15672
   - **InfluxDB UI**: http://localhost:8086

## 📋 Available Commands

| Command | Description |
|---------|-------------|
| `make setup` | Initial project setup |
| `make dev` | Start development environment |
| `make build` | Build all services |
| `make start` | Start with Docker Compose |
| `make stop` | Stop all services |
| `make logs` | Show service logs |
| `make test` | Run all tests |
| `make lint` | Run linting |
| `make clean` | Clean build artifacts |
| `make reset` | Complete reset |

## 🏢 Microservices Architecture

### Core Services

#### 🔌 Device Service (Port 3001)
- **Purpose**: Device communication and control
- **Responsibilities**:
  - MQTT message handling from edge bridge
  - Real-time device status monitoring
  - Command queue management with priority levels
  - WebSocket connections for live updates
- **Tech Stack**: Node.js, TypeScript, Socket.IO, MQTT

#### 📈 Trading Service (Port 3002)
- **Purpose**: Energy trading and price optimization
- **Responsibilities**:
  - Entsoe API integration for day-ahead prices
  - Trading strategy execution (peak shaving, arbitrage)
  - Order management and execution
  - Price forecasting and optimization
- **Tech Stack**: Node.js, TypeScript, Axios, Node-Schedule

#### 📊 Analytics Service (Port 3003)
- **Purpose**: Data analysis and reporting
- **Responsibilities**:
  - Time-series data processing
  - Performance metrics calculation
  - Report generation
  - Alert management
- **Tech Stack**: Node.js, TypeScript, InfluxDB, Lodash

#### 👤 User Service (Port 3004)
- **Purpose**: Authentication and authorization
- **Responsibilities**:
  - JWT-based authentication
  - Role-based access control
  - User profile management
  - Session management
- **Tech Stack**: Node.js, TypeScript, Passport, bcrypt

#### 🌉 Edge Bridge Service (Port 8000)
- **Purpose**: Hardware communication bridge
- **Responsibilities**:
  - Modbus RTU communication with inverter
  - Command queue serialization (critical constraint)
  - MQTT message publishing to microservices
  - Hardware fault detection and alerting
  - Real-time data collection and enhancement
- **Tech Stack**: Python, FastAPI, PyModbus, Paho-MQTT

### Infrastructure Services

- **PostgreSQL**: Transactional data storage
- **InfluxDB**: Time-series energy data
- **Redis**: Caching and session storage
- **RabbitMQ**: Inter-service messaging
- **Mosquitto MQTT**: IoT device communication
- **Nginx**: API gateway and load balancer

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL="postgresql://nattery:password@postgres:5432/nattery"
INFLUXDB_TOKEN=your-influxdb-token

# Security
JWT_SECRET=your-super-secret-jwt-key
CORS_ORIGIN=https://localhost

# External APIs
ENTSOE_API_TOKEN=your-entsoe-api-token

# Hardware (Edge Bridge)
MODBUS_PORT=/dev/ttyUSB0
MODBUS_BAUDRATE=9600
MODBUS_SLAVE_ID=1
```

### Service Ports

| Service | Port | Protocol |
|---------|------|----------|
| API Gateway | 80/443 | HTTP/HTTPS |
| Frontend | 3000 | HTTP |
| Device Service | 3001 | HTTP |
| Trading Service | 3002 | HTTP |
| Analytics Service | 3003 | HTTP |
| User Service | 3004 | HTTP |
| Edge Bridge | 8000 | HTTP |

## 🔒 Security Features

- **SSL/TLS encryption** with automatic HTTPS redirect
- **JWT-based authentication** with refresh tokens
- **Rate limiting** on API endpoints
- **CORS protection** with configurable origins
- **Security headers** (HSTS, XSS protection, etc.)
- **Input validation** with Zod schemas
- **Role-based access control**

## 📊 Data Flow Architecture

### Real-time Data Pipeline

1. **Hardware Layer**: Inverter firmware monitors battery
2. **Edge Layer**: Raspberry Pi reads Modbus data
3. **Communication Layer**: MQTT publishes to broker
4. **Service Layer**: Device service processes messages
5. **Storage Layer**: InfluxDB stores time-series data
6. **Presentation Layer**: Frontend displays real-time updates

### Command Execution Flow

1. **User Interface**: Command initiated via web app
2. **API Gateway**: Request routed to device service
3. **Command Queue**: Priority-based queue management
4. **MQTT Publishing**: Command sent to edge bridge
5. **Modbus Execution**: Serial command to inverter
6. **Status Feedback**: Confirmation via MQTT

## 🏭 Production Deployment

### Balena OS Integration

Designed for fleet management with Balena OS:

```yaml
# balena.yml
version: "2"
environment:
  - BALENA_HOST_CONFIG_gpu_mem=16
services:
  nattery:
    build: .
    privileged: true
    devices:
      - "/dev/ttyUSB0:/dev/ttyUSB0"
```

### Docker Compose Production

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🧪 Testing Strategy

### Unit Tests
```bash
yarn test                    # Run all unit tests
yarn workspace @nattery/device-service test
```

### Integration Tests
```bash
make docker-up              # Start test environment
make health                 # Verify service health
```

### End-to-End Testing

Essential services for hardware testing:
- Phase 1: Infrastructure
- Phase 2: Edge Bridge
- Phase 3: Device Service
- Phase 7: Frontend

## 📈 Monitoring & Observability

### Health Checks

All services include comprehensive health checks:
- **Database connectivity**
- **Message broker status**
- **External API availability**
- **Hardware communication**

### Logging

Structured logging with Winston:
- **JSON format** for production
- **Log levels**: error, warn, info, debug
- **Service correlation** with request IDs

### Metrics

Key performance indicators:
- **Energy throughput** (kWh/day)
- **Trading profit** (€/month)
- **System uptime** (%)
- **Response times** (ms)

## 🔄 Development Workflow

### Phase-based Implementation

The project follows a structured 9-phase implementation:

1. ✅ **Phase 1**: Project Scaffolding & Core Infrastructure
2. ✅ **Phase 2**: Edge Bridge Service (Modbus-MQTT Bridge)
3. ✅ **Phase 3**: Device Service (MQTT-WebSocket Bridge & Device Management)
4. 📋 **Phase 4**: Trading Service
5. 📋 **Phase 5**: Analytics Service
6. 📋 **Phase 6**: User Service
7. 📋 **Phase 7**: Frontend Service
8. 📋 **Phase 8**: Monitoring & Observability
9. 📋 **Phase 9**: Balena OS Integration

### Git Workflow

```bash
git checkout -b feature/phase-2-edge-bridge
# Implement feature
git commit -m "feat: implement edge bridge service"
git push origin feature/phase-2-edge-bridge
# Create pull request
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Follow TypeScript and ESLint conventions**
4. **Add tests for new functionality**
5. **Update documentation**
6. **Submit a pull request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: [https://github.com/x-2b/nattery-battery-trading](https://github.com/x-2b/nattery-battery-trading)
- **Issues**: [https://github.com/x-2b/nattery-battery-trading/issues](https://github.com/x-2b/nattery-battery-trading/issues)
- **Documentation**: [Implementation Phases](IMPLEMENTATION_PHASES.md)
- **Inverter Datasheet**: [inverter-datasheet.md](inverter-datasheet.md)

---

**Built with ❤️ for sustainable energy trading** 