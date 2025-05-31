# Nattery Battery Energy Trading System
# Development and Deployment Makefile

.PHONY: help setup dev build start stop restart logs clean test lint type-check docker-build docker-up docker-down reset edge-bridge-dev edge-bridge-logs edge-bridge-shell edge-bridge-test device-service-dev device-service-logs device-service-shell device-service-test device-service-db-migrate device-service-db-generate device-service-db-studio

# Default target
help:
	@echo "Nattery Battery Energy Trading System"
	@echo "====================================="
	@echo ""
	@echo "Available commands:"
	@echo "  setup        - Initial project setup (install dependencies, build types)"
	@echo "  dev          - Start development environment"
	@echo "  build        - Build all services"
	@echo "  start        - Start all services with Docker Compose"
	@echo "  stop         - Stop all services"
	@echo "  restart      - Restart all services"
	@echo "  logs         - Show logs from all services"
	@echo "  clean        - Clean build artifacts"
	@echo "  test         - Run tests for all services"
	@echo "  lint         - Run linting for all services"
	@echo "  type-check   - Run TypeScript type checking"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up    - Start services with Docker Compose"
	@echo "  docker-down  - Stop and remove Docker containers"
	@echo "  reset        - Complete reset (remove containers, volumes, clean build)"
	@echo "  edge-bridge-dev - Start Edge Bridge in development mode"
	@echo "  edge-bridge-logs - Show Edge Bridge logs"
	@echo "  edge-bridge-shell - Access Edge Bridge container shell"
	@echo "  edge-bridge-test - Test Edge Bridge connectivity"
	@echo "  device-service-dev - Start Device Service in development mode"
	@echo "  device-service-logs - Show Device Service logs"
	@echo "  device-service-shell - Access Device Service container shell"
	@echo "  device-service-test - Test Device Service connectivity"
	@echo "  device-service-db-migrate - Run Device Service database migrations"
	@echo "  device-service-db-generate - Generate Device Service Prisma client"
	@echo "  device-service-db-studio - Open Device Service Prisma Studio"

# Initial setup
setup:
	@echo "Setting up Nattery project..."
	yarn install
	yarn build:types
	@echo "Setup complete!"

# Development
dev:
	@echo "Starting development environment..."
	yarn dev

# Build
build:
	@echo "Building all services..."
	yarn build

build-types:
	@echo "Building shared types..."
	yarn build:types

build-services:
	@echo "Building backend services..."
	yarn build:services

build-frontend:
	@echo "Building frontend..."
	yarn build:frontend

# Docker operations
start:
	@echo "Starting all services..."
	docker-compose up -d

stop:
	@echo "Stopping all services..."
	docker-compose down

restart:
	@echo "Restarting all services..."
	docker-compose restart

logs:
	@echo "Showing logs from all services..."
	docker-compose logs -f

# Quality assurance
clean:
	@echo "Cleaning build artifacts..."
	yarn clean

test:
	@echo "Running tests..."
	yarn test

lint:
	@echo "Running linting..."
	yarn lint

type-check:
	@echo "Running TypeScript type checking..."
	yarn type-check

# Docker specific
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d

docker-down:
	@echo "Stopping and removing Docker containers..."
	docker-compose down -v

# Complete reset
reset:
	@echo "Performing complete reset..."
	docker-compose down -v
	docker system prune -f
	yarn clean
	yarn install
	@echo "Reset complete!"

# Environment setup
env:
	@echo "Setting up environment file..."
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file from env.example"; \
		echo "Please update the environment variables in .env"; \
	else \
		echo ".env file already exists"; \
	fi

# MQTT password generation
mqtt-passwd:
	@echo "Generating MQTT password file..."
	docker run --rm -v $(PWD)/mosquitto/config:/config eclipse-mosquitto:2.0 mosquitto_passwd -c /config/passwd nattery

# Database operations
db-migrate:
	@echo "Running database migrations..."
	yarn workspace @nattery/device-service prisma migrate dev
	yarn workspace @nattery/trading-service prisma migrate dev
	yarn workspace @nattery/analytics-service prisma migrate dev
	yarn workspace @nattery/user-service prisma migrate dev

db-reset:
	@echo "Resetting databases..."
	yarn workspace @nattery/device-service prisma migrate reset --force
	yarn workspace @nattery/trading-service prisma migrate reset --force
	yarn workspace @nattery/analytics-service prisma migrate reset --force
	yarn workspace @nattery/user-service prisma migrate reset --force

# Health check
health:
	@echo "Checking service health..."
	@curl -f http://localhost/health || echo "Gateway not responding"
	@curl -f http://localhost:3001/health || echo "Device service not responding"
	@curl -f http://localhost:3002/health || echo "Trading service not responding"
	@curl -f http://localhost:3003/health || echo "Analytics service not responding"
	@curl -f http://localhost:3004/health || echo "User service not responding"

# Edge Bridge specific commands
edge-bridge-dev: ## Start Edge Bridge in development mode
	@echo "Starting Edge Bridge Service in development mode..."
	cd services/edge-bridge && python main.py

edge-bridge-logs: ## Show Edge Bridge logs
	docker-compose logs -f edge-bridge

edge-bridge-shell: ## Access Edge Bridge container shell
	docker-compose exec edge-bridge /bin/bash

edge-bridge-test: ## Test Edge Bridge connectivity
	@echo "Testing Edge Bridge connectivity..."
	curl -f http://localhost:8000/health || echo "Edge Bridge not responding"
	curl -f http://localhost:8000/status || echo "Edge Bridge status unavailable"

# Device Service specific commands
device-service-dev: ## Start Device Service in development mode
	@echo "Starting Device Service in development mode..."
	cd services/device-service && yarn dev

device-service-logs: ## Show Device Service logs
	docker-compose logs -f device-service

device-service-shell: ## Access Device Service container shell
	docker-compose exec device-service /bin/sh

device-service-test: ## Test Device Service connectivity
	@echo "Testing Device Service connectivity..."
	curl -f http://localhost:3001/health || echo "Device Service not responding"
	curl -f http://localhost:3001/api/health || echo "Device Service API not responding"

device-service-db-migrate: ## Run Device Service database migrations
	@echo "Running Device Service database migrations..."
	cd services/device-service && yarn prisma migrate dev

device-service-db-generate: ## Generate Device Service Prisma client
	@echo "Generating Device Service Prisma client..."
	cd services/device-service && yarn prisma generate

device-service-db-studio: ## Open Device Service Prisma Studio
	@echo "Opening Device Service Prisma Studio..."
	cd services/device-service && yarn prisma studio 