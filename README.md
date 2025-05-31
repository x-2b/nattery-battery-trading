# Nattery - Battery Energy Trading System

A scalable microservices-based application for controlling and monitoring house batteries to enable energy trading through peak shaving and arbitrage opportunities.

## 🏗️ System Architecture Overview

### Data Flow
```
Battery ← Inverter (Firmware) ← Modbus RTU ← USB Converter ← Raspberry Pi ← MQTT ← Microservices ← Web App
```

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  Next.js 14 + TypeScript + Tailwind CSS + Shadcn/ui             │ 
│  - Real-time battery monitoring dashboard                       │
│  - Energy trading controls and strategies                       │
│  - Analytics, reporting, and performance metrics                │
│  - Alert management and system health monitoring                │
└─────────────────────────────────────────────────────────────────┘
                                │ WebSocket + REST API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (Nginx)                        │
├─────────────────────────────────────────────────────────────────┤
│  - Load balancing across microservices                          │
│  - Authentication and authorization                             │
│  - Rate limiting and API protection                             │
│  - WebSocket proxy for real-time communication                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Microservices Layer                          │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│  Device Service │ Trading Service │ Analytics Svc   │ User Svc  │
│                 │                 │                 │           │
│ • Inverter comm │ • Market data   │ • Energy usage  │ • Auth    │
│ • Battery mon   │ • Trading algos │ • Performance   │ • Profile │
│ • Commands      │ • Peak shaving  │ • Predictions   │ • Settings│
│ • Health check  │ • Arbitrage     │ • Reporting     │ • Alerts  │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Message Broker Layer                         │
│  ┌─────────────┬─────────────────┬─────────────────────────────┐ │
│  │    MQTT     │    RabbitMQ     │         Redis               │ │
│  │ (IoT Comms) │ (Service Msgs)  │    (Caching/Sessions)       │ │
│  │             │                 │                             │ │
│  │ • Telemetry │ • Trading Events│ • User Sessions             │ │
│  │ • Commands  │ • Notifications │ • API Caching               │ │
│  │ • Alerts    │ • Job Queues    │ • Real-time Data            │ │
│  └─────────────┴─────────────────┴─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌─────────────────────────────┬─────────────────────────────┐   │
│  │        PostgreSQL           │         InfluxDB            │   │
│  │    (Transactional Data)     │     (Time-Series Data)      │   │
│  │                             │                             │   │
│  │ • User accounts & settings  │ • Battery telemetry         │   │
│  │ • Trading strategies        │ • Power measurements        │   │
│  │ • Trading orders & history  │ • Energy flow data          │   │
│  │ • System configuration      │ • Performance metrics       │   │
│  └─────────────────────────────┴─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Edge Layer (Raspberry Pi)                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Modbus-MQTT Bridge Service                     │ │
│  │                                                             │ │
│  │ • Modbus RTU communication (9600 baud, RS485)               │ │
│  │ • Command queue management (serialized access)              │ │
│  │ • Telemetry publishing to MQTT                              │ │
│  │ • Health monitoring and error recovery                      │ │
│  │ • Local data buffering and retry logic                      │ │
│  │                                                             │ │
│  │ **Note:** The Edge Bridge is the ONLY component with direct │ │
│  │ Modbus access. All other services interact via MQTT.        │ │
│  │ **Strictly Serialized Modbus Access:** All Modbus commands  │ │
│  │ are queued and executed one at a time to ensure protocol    │ │
│  │ compliance and device safety.                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │ Modbus RTU (Single Serial Connection)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Hardware Layer                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Inverter System                          │ │
│  │                                                             │ │
│  │ • Battery management and control (via firmware)             │ │
│  │ • PV input management and MPPT                              │ │
│  │ • Grid connection monitoring and control                    │ │
│  │ • Load output management                                    │ │
│  │ • Safety and protection systems                             │ │
│  │                                                             │ │
│  │ Connected Battery: Fully managed by inverter firmware       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚦 How It Works

1. **User Action**: User issues a command (e.g., discharge battery) via the web app.
2. **API Gateway**: The command is routed through the API Gateway to the appropriate microservice.
3. **Service Layer**: The relevant service (e.g., Trading or Device Service) publishes the command to MQTT.
4. **Edge Bridge**: The edge bridge receives the command, queues it, and executes it via Modbus RTU (one at a time).
5. **Inverter**: The inverter acts on the command, and telemetry is sent back through the same path for real-time feedback to the user.

---

## 🐳 Containerized Microservices Architecture

### Core Principles
- **Single Responsibility**: Each service handles one business domain
- **Independent Deployment**: Services can be deployed and scaled independently
- **Technology Agnostic**: Services can use different tech stacks
- **Fault Isolation**: Failure in one service doesn't affect others
- **Balena OS Ready**: All services containerized for edge deployment

### Service Breakdown

#### 1. **Frontend Service** (`frontend/`)
- **Technology**: Next.js 14, TypeScript, Tailwind CSS
- **Purpose**: User interface for monitoring and control
- **Container**: Single-page application with Nginx
- **Ports**: 3000
- **Dependencies**: API Gateway

#### 2. **API Gateway** (`gateway/`)
- **Technology**: Nginx with custom configuration
- **Purpose**: Request routing, authentication, load balancing
- **Container**: Nginx with SSL termination
- **Ports**: 80, 443
- **Dependencies**: All backend services

#### 3. **Device Service** (`services/device-service/`)
- **Technology**: Node.js + TypeScript
- **Purpose**: Inverter communication and device management
- **Container**: Node.js runtime
- **Ports**: 3001
- **Dependencies**: MQTT, PostgreSQL, InfluxDB

#### 4. **Trading Service** (`services/trading-service/`)
- **Technology**: Node.js + TypeScript
- **Purpose**: Energy trading algorithms and market data
- **Container**: Node.js runtime
- **Ports**: 3002
- **Dependencies**: MQTT, PostgreSQL, RabbitMQ

#### 5. **Analytics Service** (`services/analytics-service/`)
- **Technology**: Node.js + TypeScript
- **Purpose**: Data analysis, reporting, and predictions
- **Container**: Node.js runtime
- **Ports**: 3003
- **Dependencies**: PostgreSQL, InfluxDB

#### 6. **User Service** (`services/user-service/`)
- **Technology**: Node.js + TypeScript
- **Purpose**: Authentication, user management, settings
- **Container**: Node.js runtime
- **Ports**: 3004
- **Dependencies**: PostgreSQL, Redis

#### 7. **Edge Bridge Service** (`edge/modbus-bridge/`)
- **Technology**: Python 3.11
- **Purpose**: Modbus-MQTT bridge with command queuing
- **Container**: Python runtime with serial access
- **Ports**: N/A (serial communication)
- **Dependencies**: MQTT, USB/Serial device access
- **Note**: The Edge Bridge is the only component with direct Modbus access. All other services interact with the inverter via MQTT.
- **Strictly Serialized Modbus Access**: All Modbus commands are queued and executed one at a time to ensure protocol compliance and device safety.

### Infrastructure Services

#### 8. **MQTT Broker** (`infrastructure/mqtt/`)
- **Technology**: Eclipse Mosquitto
- **Purpose**: IoT device communication
- **Container**: Official Mosquitto image
- **Ports**: 1883 (MQTT), 9001 (WebSocket)

#### 9. **Message Queue** (`infrastructure/rabbitmq/`)
- **Technology**: RabbitMQ
- **Purpose**: Service-to-service messaging
- **Container**: Official RabbitMQ image
- **Ports**: 5672 (AMQP), 15672 (Management)

#### 10. **Cache & Sessions** (`infrastructure/redis/`)
- **Technology**: Redis
- **Purpose**: Caching and session management
- **Container**: Official Redis image
- **Ports**: 6379

#### 11. **Primary Database** (`infrastructure/postgres/`)
- **Technology**: PostgreSQL 15
- **Purpose**: Transactional data storage
- **Container**: Official PostgreSQL image
- **Ports**: 5432

#### 12. **Time-Series Database** (`infrastructure/influxdb/`)
- **Technology**: InfluxDB 2.7
- **Purpose**: Telemetry and metrics storage
- **Container**: Official InfluxDB image
- **Ports**: 8086

#### 13. **Monitoring** (`infrastructure/monitoring/`)
- **Technology**: Prometheus + Grafana
- **Purpose**: System monitoring and alerting
- **Containers**: Prometheus, Grafana
- **Ports**: 9090 (Prometheus), 3000 (Grafana)

## 🚀 Key Features

### Energy Trading Capabilities
- **Peak Shaving**: Automatically discharge during peak demand hours
- **Arbitrage Trading**: Buy low, sell high based on energy market prices
- **Grid Services**: Frequency regulation and demand response
- **Solar Optimization**: Maximize self-consumption of PV generation

### Real-Time Monitoring
- **Battery Status**: SOC, voltage, current, power, temperature
- **Energy Flow**: PV generation, grid import/export, load consumption
- **System Health**: Inverter status, alarms, communication health
- **Performance Metrics**: Trading efficiency, energy savings

### Advanced Control
- **Remote Commands**: Charge/discharge control via web interface
- **Automated Strategies**: Configurable trading algorithms
- **Time-Based Control**: Scheduled charging/discharging windows
- **Emergency Controls**: Safety shutdowns and fault management

## 📁 Project Structure

```
nattery-2/
├── frontend/                    # Next.js web application
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── gateway/                     # Nginx API gateway
│   ├── Dockerfile
│   └── nginx.conf
├── services/
│   ├── device-service/          # Inverter communication
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── src/
│   ├── trading-service/         # Energy trading logic
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── src/
│   ├── analytics-service/       # Data analysis & reporting
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── src/
│   └── user-service/            # Authentication & user management
│       ├── Dockerfile
│       ├── package.json
│       └── src/
├── edge/
│   └── modbus-bridge/           # Raspberry Pi edge service
│       ├── Dockerfile
│       ├── requirements.txt
│       └── src/
├── infrastructure/
│   ├── mqtt/                    # MQTT broker configuration
│   ├── postgres/                # Database initialization
│   ├── monitoring/              # Prometheus & Grafana
│   └── balena/                  # Balena OS deployment configs
├── shared/
│   ├── types/                   # TypeScript type definitions
│   └── utils/                   # Common utilities
├── docker-compose.yml           # Local development
├── docker-compose.balena.yml    # Balena OS deployment
└── balena.yml                   # Balena application configuration
```

## 🔧 Balena OS Deployment

### Fleet Management
- **Multi-Device Support**: Deploy to entire battery fleet
- **Over-the-Air Updates**: Remote updates without physical access
- **Device Monitoring**: Real-time fleet health monitoring
- **Configuration Management**: Environment variables per device/fleet

### Balena Configuration (`balena.yml`)
```yaml
version: "2"
environment:
  - FLEET_NAME=nattery-battery-fleet
  - DEVICE_TYPE=raspberrypi4-64
services:
  - frontend
  - gateway
  - device-service
  - trading-service
  - analytics-service
  - user-service
  - modbus-bridge
  - mqtt
  - redis
  - postgres
  - influxdb
```

### Device-Specific Configuration
- **Serial Port Access**: USB-to-RS485 converter configuration
- **Network Settings**: WiFi/Ethernet configuration per site
- **Security**: Device-specific certificates and credentials
- **Local Storage**: Persistent data volumes for databases

## 🔒 Security Architecture

### Edge Security
- **Device Authentication**: Unique certificates per device
- **Encrypted Communication**: TLS for all MQTT communication
- **Local Firewall**: Restricted network access
- **Secure Boot**: Balena OS security features

### Service Security
- **JWT Authentication**: Stateless authentication tokens
- **Role-Based Access**: Admin, operator, viewer roles
- **API Rate Limiting**: Protection against abuse
- **Input Validation**: Comprehensive data validation

### Network Security
- **VPN Access**: Secure remote access to devices
- **Network Segmentation**: Isolated device networks
- **Certificate Management**: Automated certificate rotation
- **Audit Logging**: Complete audit trail

## 📊 Monitoring & Observability

### System Metrics
- **Device Health**: CPU, memory, disk, temperature
- **Communication Health**: Modbus, MQTT, network status
- **Service Performance**: Response times, error rates
- **Business Metrics**: Energy traded, savings, efficiency

### Alerting
- **Critical Alerts**: System failures, communication loss
- **Warning Alerts**: Performance degradation, high usage
- **Business Alerts**: Trading opportunities, anomalies
- **Maintenance Alerts**: Scheduled maintenance reminders

## 🌐 External Integrations

### Energy Market APIs
- **Real-Time Pricing**: Live energy market data
- **Forecast Data**: Price predictions and trends
- **Grid Status**: Utility grid conditions
- **Regulatory Data**: Compliance and reporting

### Weather & Solar
- **Weather Forecasts**: Solar generation predictions
- **Irradiance Data**: Real-time solar conditions
- **Climate Data**: Long-term planning data

## 🚦 Development Workflow

### Local Development
```bash
# Start all services locally
docker-compose up -d

# Start individual service for development
docker-compose up device-service

# View logs
docker-compose logs -f trading-service
```

### Balena Deployment
```bash
# Deploy to fleet
balena push nattery-fleet

# Deploy to specific device
balena push <device-uuid>

# Monitor deployment
balena logs <device-uuid>
```

### Testing Strategy
- **Unit Tests**: Individual service testing
- **Integration Tests**: Service-to-service communication
- **End-to-End Tests**: Complete workflow testing
- **Load Tests**: Performance under high load

## 📈 Scalability Considerations

### Horizontal Scaling
- **Service Replication**: Multiple instances per service
- **Load Balancing**: Distribute requests across instances
- **Database Sharding**: Partition data across databases
- **Geographic Distribution**: Regional deployments

### Performance Optimization
- **Caching Strategy**: Multi-level caching
- **Database Optimization**: Indexing and query optimization
- **Message Queuing**: Asynchronous processing
- **CDN Integration**: Static asset delivery

## 🔄 Data Flow Architecture

### Telemetry Flow
1. **Inverter** → Modbus RTU → **Edge Bridge**
2. **Edge Bridge** → MQTT → **Device Service**
3. **Device Service** → InfluxDB (storage) + MQTT (real-time)
4. **Frontend** ← WebSocket ← **API Gateway** ← Services

### Command Flow
1. **Frontend** → REST API → **API Gateway**
2. **API Gateway** → **Trading/Device Service**
3. **Service** → MQTT → **Edge Bridge**
4. **Edge Bridge** → Command Queue → Modbus RTU → **Inverter**

### Event Flow
1. **Services** → RabbitMQ → **Other Services**
2. **Analytics Service** → Scheduled Reports
3. **Alert Service** → Notifications → **Users**

---

## 📝 Design Decisions & Limitations

### Why MQTT?
- **IoT-Native**: MQTT is lightweight, reliable, and designed for device-to-cloud communication, making it ideal for edge devices like Raspberry Pi.
- **Publish/Subscribe**: Enables real-time telemetry and command distribution to multiple services and UIs.
- **Fleet Scalability**: Easily supports large numbers of devices and services.

### Why Strict Modbus Serialization?
- **Protocol Limitation**: Modbus RTU is strictly single-master and synchronous; concurrent or async access is not possible.
- **Reliability & Safety**: Serializing all Modbus commands in a queue ensures safe, predictable operation and prevents communication errors or device faults.
- **Edge Bridge Role**: Only the edge bridge service communicates with the inverter over Modbus; all other services interact via MQTT.

### Why Containerize Everything?
- **Service Isolation**: Each microservice runs in its own container for fault isolation and independent scaling.
- **Balena OS Compatibility**: Containerization is required for seamless deployment, updates, and management across a distributed battery fleet.
- **Technology Flexibility**: Allows each service to use the best-fit language and runtime.

### Why Not Monolithic?
- **Maintainability**: Microservices are easier to develop, test, and maintain independently.
- **Scalability**: Services can be scaled horizontally as needed.
- **Resilience**: Failures are isolated to individual services, not the whole system.

---

This architecture provides a robust, scalable foundation for battery energy trading while maintaining simplicity in individual services and enabling efficient fleet management through Balena OS. 