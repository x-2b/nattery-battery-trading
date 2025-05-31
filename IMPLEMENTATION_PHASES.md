# Implementation Phases for Nattery Battery Energy Trading System

This document breaks down the project into clear, self-contained implementation phases. Each phase is designed to be handled by an AI coding agent, with relevant context and awareness of the overall architecture. Each phase includes a description, goals, dependencies, and context links to the overall system.

---

## Phase 1: Project Scaffolding & Core Infrastructure

**Description:**
- Set up the foundational project structure, monorepo, and core infrastructure services (MQTT, RabbitMQ, Redis, PostgreSQL, InfluxDB, Prometheus, Grafana, Nginx API Gateway).

**Goals:**
- Create the directory structure as described in the README.
- Write Dockerfiles and docker-compose files for all services and infrastructure.
- Ensure all containers can be built and started together.
- Provide basic health checks for each service.

**Dependencies:**
- None (starting point for the project).

**Context:**
- Refer to the architecture and project structure in `README.md`.
- This phase enables all subsequent development and testing.

---

## Phase 2: Edge Bridge Service (Modbus-MQTT Bridge)

**Description:**
- Implement the Python-based edge service that communicates with the inverter over Modbus RTU and bridges data/commands to MQTT.

**Goals:**
- Establish Modbus RTU communication (single serial connection, 9600 baud, RS485).
- Implement a strict command queue for serialized Modbus access.
- **All Modbus commands must be strictly sequential (no concurrency) due to inverter firmware limitations.**
- Periodically poll inverter registers for telemetry and publish to MQTT topics.
- Subscribe to MQTT command topics, queue, and execute commands via Modbus.
- Handle error recovery, local buffering, and health monitoring.

**Dependencies:**
- Phase 1 (infrastructure, MQTT broker must be running).

**Context:**
- See "Edge Layer (Raspberry Pi)" in `README.md`.
- See inverter register map and firmware limitations in `inverter-datasheet.md`.
- All other services interact with the inverter only via MQTT.

---

## Phase 3: Device Service (Backend Microservice)

**Description:**
- Implement the Node.js/TypeScript service that manages device state, processes telemetry, and exposes device APIs.

**Goals:**
- Subscribe to relevant MQTT topics for inverter telemetry and command results.
- Store telemetry in InfluxDB and device metadata in PostgreSQL.
- Expose REST and WebSocket APIs for device status, health, and control.
- Forward user commands (from API) to MQTT for the edge bridge.
- Implement alerting for device faults and communication issues.

**Dependencies:**
- Phase 1 (infrastructure), Phase 2 (edge bridge must be publishing telemetry).

**Context:**
- See "Device Service" and "Data Layer" in `README.md`.
- See MQTT topic structure in the architecture section.
- Device Service is the main backend for device monitoring and control.

---

## Phase 4: Trading Service (Backend Microservice)

**Description:**
- Implement the Node.js/TypeScript service that runs energy trading algorithms and manages trading operations.

**Goals:**
- Ingest real-time telemetry from Device Service (via events or direct MQTT subscription).
- Integrate with external energy market APIs for price data, specifically Entsoe for day-ahead prices.
- Handle Entsoe's once-daily update after 15:00, using a secure token, and account for endpoint latency (5s to 1min, especially on first request).
- Cache and persist day-ahead prices for use in trading strategies.
- Implement trading strategies (peak shaving, arbitrage, etc.) using the latest available price data.
- Generate and send trading commands to Device Service (and thus to the inverter via MQTT).
- Store trading history and performance metrics in PostgreSQL.

**Dependencies:**
- Phase 1 (infrastructure), Phase 3 (device service must be operational).

**Context:**
- See "Trading Service" and "Energy Trading Capabilities" in `README.md`.
- Trading Service is responsible for all automated and user-initiated trading logic.
- See "Design Considerations: Entsoe Integration" at the end of this file.

---

## Phase 5: Analytics Service (Backend Microservice)

**Description:**
- Implement the Node.js/TypeScript service for analytics, reporting, and predictions.

**Goals:**
- Aggregate and analyze time-series data from InfluxDB and trading data from PostgreSQL.
- Provide APIs for historical analytics, performance reports, and forecasts.
- Support scheduled and on-demand report generation.
- Integrate with alerting and notification systems.

**Dependencies:**
- Phase 1 (infrastructure), Phase 3 (device data), Phase 4 (trading data).

**Context:**
- See "Analytics Service" and "Monitoring & Observability" in `README.md`.
- Analytics Service provides insights for users and system optimization.

---

## Phase 6: User Service (Backend Microservice)

**Description:**
- Implement the Node.js/TypeScript service for authentication, user management, and settings.

**Goals:**
- Provide JWT-based authentication and role-based access control.
- Manage user profiles, preferences, and notification settings.
- Integrate with Redis for session management.
- Expose APIs for user registration, login, and management.

**Dependencies:**
- Phase 1 (infrastructure).

**Context:**
- See "User Service" and "Security Architecture" in `README.md`.
- User Service is the entry point for all user-related operations.

---

## Phase 7: Frontend Service (Web Application)

**Description:**
- Implement the Next.js/TypeScript web application for user interaction.

**Goals:**
- Provide real-time dashboards for battery/inverter status and trading activity.
- Enable users to view analytics, configure trading strategies, and send commands.
- Integrate with all backend APIs and WebSocket endpoints.
- Support authentication and role-based access.
- Ensure responsive, user-friendly design with Tailwind CSS and Shadcn/ui.
- Display day-ahead prices and trading recommendations based on Entsoe data.
- **Provide an advanced UI to control and monitor the most relevant inverter registers, with real-time updates and user-friendly controls.**

**Dependencies:**
- Phase 1 (infrastructure), Phases 3-6 (backend APIs).

**Context:**
- See "Frontend Layer" and "Key Features" in `README.md`.
- See `inverter-datasheet.md` for register details to be surfaced in the UI.
- Frontend is the main user interface for the system.

---

## Phase 8: Monitoring, Alerting & Observability

**Description:**
- Implement system-wide monitoring, alerting, and observability using Prometheus, Grafana, and service-level health checks.

**Goals:**
- Collect metrics from all services and infrastructure.
- Set up dashboards for system health, device status, and trading performance.
- Configure alerting rules for critical events and anomalies.
- Integrate alert notifications with user service and external channels (email, SMS, etc.).
- Monitor Entsoe API fetches and alert on failures or excessive latency.

**Dependencies:**
- Phase 1 (infrastructure), all other phases (for metrics sources).

**Context:**
- See "Monitoring & Observability" in `README.md`.
- This phase ensures operational reliability and rapid incident response.

---

## Phase 9: Balena OS Integration & Fleet Management

**Description:**
- Prepare all services for deployment on Balena OS, enabling fleet management and over-the-air updates.

**Goals:**
- Write and test Balena-specific Dockerfiles and configuration files.
- Ensure all services can be deployed, updated, and monitored via Balena Cloud.
- Implement device-specific configuration (serial ports, network, security).
- Document deployment and update procedures for fleet operators.

**Dependencies:**
- All previous phases (services must be containerized and functional).

**Context:**
- See "Balena OS Deployment" and "Fleet Management" in `README.md`.
- This phase enables scalable, maintainable deployment to a distributed battery fleet.

---

## Design Considerations: Entsoe Integration & Modbus Sequentiality

- **Day-Ahead Prices**: The Trading Service must fetch day-ahead prices from Entsoe using a secure token. These prices are updated once daily after 15:00 and are critical for optimal trading strategies.
- **API Latency**: The Entsoe endpoint can be slow (5s to 1min, especially on the first request). The system should use asynchronous fetching, retries, and caching to ensure price data is available when needed.
- **Fetch Scheduling**: Implement a scheduled job to fetch prices shortly after 15:00 each day, with retry logic and alerting on failure or excessive latency.
- **Token Security**: Store the Entsoe security token securely (e.g., environment variable, secret manager) and never expose it to the frontend or logs.
- **Data Persistence**: Cache and persist the latest day-ahead prices in the database for use by trading algorithms and for display in the frontend.
- **Frontend Awareness**: The frontend should display the latest available prices and indicate if prices are stale or unavailable.
- **Monitoring**: Monitor the health and latency of Entsoe API fetches and alert operators if there are issues.
- **Modbus Sequentiality**: The inverter firmware cannot handle concurrent Modbus commands. All Modbus operations must be strictly sequential, enforced by the edge bridge service. This is critical for system stability and must be respected in all design and implementation phases. See `inverter-datasheet.md` for protocol and register details.

---

Each phase is designed to be self-contained for an AI coding agent, with clear context and dependencies. For best results, provide the agent with this file, the `README.md`, and any relevant service or datasheet documentation for its assigned phase. 