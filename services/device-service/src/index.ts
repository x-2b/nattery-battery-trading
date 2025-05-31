/**
 * Nattery Device Service
 * 
 * Main entry point for the device communication and monitoring service.
 * Handles MQTT communication with Edge Bridge, WebSocket connections for real-time updates,
 * and device data processing and storage.
 */

import express from 'express';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';

import { logger } from './utils/logger';
import { config } from './config/config';
import { DatabaseManager } from './database/DatabaseManager';
import { RedisManager } from './cache/RedisManager';
import { MQTTManager } from './mqtt/MQTTManager';
import { RabbitMQManager } from './messaging/RabbitMQManager';
import { DeviceManager } from './services/DeviceManager';
import { DataProcessor } from './services/DataProcessor';
import { CommandManager } from './services/CommandManager';
import { WebSocketManager } from './websocket/WebSocketManager';
import { HealthMonitor } from './monitoring/HealthMonitor';

// Routes
import deviceRoutes from './routes/deviceRoutes';
import dataRoutes from './routes/dataRoutes';
import commandRoutes from './routes/commandRoutes';
import healthRoutes from './routes/healthRoutes';

// Load environment variables
dotenv.config();

class DeviceService {
  private app: express.Application;
  private server: any;
  private io: SocketIOServer;
  private databaseManager: DatabaseManager;
  private redisManager: RedisManager;
  private mqttManager: MQTTManager;
  private rabbitMQManager: RabbitMQManager;
  private deviceManager: DeviceManager;
  private dataProcessor: DataProcessor;
  private commandManager: CommandManager;
  private webSocketManager: WebSocketManager;
  private healthMonitor: HealthMonitor;

  constructor() {
    this.app = express();
    this.server = createServer(this.app);
    this.io = new SocketIOServer(this.server, {
      cors: {
        origin: config.cors.origin,
        methods: ['GET', 'POST'],
        credentials: true
      }
    });

    this.initializeMiddleware();
    this.initializeRoutes();
  }

  private initializeMiddleware(): void {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          scriptSrc: ["'self'"],
          imgSrc: ["'self'", "data:", "https:"],
        },
      },
    }));

    // CORS
    this.app.use(cors({
      origin: config.cors.origin,
      credentials: true
    }));

    // Compression
    this.app.use(compression());

    // Rate limiting
    const limiter = rateLimit({
      windowMs: config.rateLimit.windowMs,
      max: config.rateLimit.maxRequests,
      message: 'Too many requests from this IP, please try again later.',
      standardHeaders: true,
      legacyHeaders: false,
    });
    this.app.use('/api/', limiter);

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Request logging
    this.app.use((req, res, next) => {
      logger.info(`${req.method} ${req.path}`, {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        requestId: req.headers['x-request-id']
      });
      next();
    });
  }

  private initializeRoutes(): void {
    // API routes
    this.app.use('/api/devices', deviceRoutes);
    this.app.use('/api/data', dataRoutes);
    this.app.use('/api/commands', commandRoutes);
    this.app.use('/api/health', healthRoutes);

    // Root health check
    this.app.get('/health', (req, res) => {
      res.json({
        service: 'device-service',
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: process.env.npm_package_version || '1.0.0'
      });
    });

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Not Found',
        message: `Route ${req.originalUrl} not found`,
        timestamp: new Date().toISOString()
      });
    });

    // Error handler
    this.app.use((error: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
      logger.error('Unhandled error:', error);
      
      res.status(error.status || 500).json({
        error: 'Internal Server Error',
        message: config.nodeEnv === 'development' ? error.message : 'Something went wrong',
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id']
      });
    });
  }

  public async initialize(): Promise<void> {
    try {
      logger.info('Initializing Device Service...');

      // Initialize database connections
      this.databaseManager = new DatabaseManager();
      await this.databaseManager.initialize();
      logger.info('Database connections established');

      // Initialize Redis
      this.redisManager = new RedisManager();
      await this.redisManager.connect();
      logger.info('Redis connection established');

      // Initialize RabbitMQ
      this.rabbitMQManager = new RabbitMQManager();
      await this.rabbitMQManager.connect();
      logger.info('RabbitMQ connection established');

      // Initialize core services
      this.deviceManager = new DeviceManager(this.databaseManager, this.redisManager);
      this.dataProcessor = new DataProcessor(this.databaseManager, this.redisManager);
      this.commandManager = new CommandManager(this.databaseManager, this.redisManager, this.rabbitMQManager);

      // Initialize WebSocket manager
      this.webSocketManager = new WebSocketManager(this.io);
      logger.info('WebSocket server initialized');

      // Initialize MQTT manager (connects to Edge Bridge)
      this.mqttManager = new MQTTManager(
        this.deviceManager,
        this.dataProcessor,
        this.commandManager,
        this.webSocketManager
      );
      await this.mqttManager.connect();
      logger.info('MQTT connection established');

      // Initialize health monitor
      this.healthMonitor = new HealthMonitor(
        this.databaseManager,
        this.redisManager,
        this.mqttManager,
        this.rabbitMQManager
      );
      await this.healthMonitor.start();
      logger.info('Health monitoring started');

      logger.info('Device Service initialization complete');

    } catch (error) {
      logger.error('Failed to initialize Device Service:', error);
      throw error;
    }
  }

  public async start(): Promise<void> {
    try {
      await this.initialize();

      this.server.listen(config.port, () => {
        logger.info(`Device Service started on port ${config.port}`, {
          environment: config.nodeEnv,
          port: config.port,
          cors: config.cors.origin
        });
      });

      // Graceful shutdown handlers
      process.on('SIGTERM', () => this.gracefulShutdown('SIGTERM'));
      process.on('SIGINT', () => this.gracefulShutdown('SIGINT'));
      process.on('uncaughtException', (error) => {
        logger.error('Uncaught Exception:', error);
        this.gracefulShutdown('uncaughtException');
      });
      process.on('unhandledRejection', (reason, promise) => {
        logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
        this.gracefulShutdown('unhandledRejection');
      });

    } catch (error) {
      logger.error('Failed to start Device Service:', error);
      process.exit(1);
    }
  }

  private async gracefulShutdown(signal: string): Promise<void> {
    logger.info(`Received ${signal}, starting graceful shutdown...`);

    try {
      // Stop accepting new connections
      this.server.close(() => {
        logger.info('HTTP server closed');
      });

      // Close WebSocket connections
      if (this.webSocketManager) {
        await this.webSocketManager.close();
        logger.info('WebSocket connections closed');
      }

      // Disconnect from MQTT
      if (this.mqttManager) {
        await this.mqttManager.disconnect();
        logger.info('MQTT connection closed');
      }

      // Close RabbitMQ connection
      if (this.rabbitMQManager) {
        await this.rabbitMQManager.disconnect();
        logger.info('RabbitMQ connection closed');
      }

      // Close Redis connection
      if (this.redisManager) {
        await this.redisManager.disconnect();
        logger.info('Redis connection closed');
      }

      // Close database connections
      if (this.databaseManager) {
        await this.databaseManager.close();
        logger.info('Database connections closed');
      }

      // Stop health monitor
      if (this.healthMonitor) {
        await this.healthMonitor.stop();
        logger.info('Health monitor stopped');
      }

      logger.info('Graceful shutdown complete');
      process.exit(0);

    } catch (error) {
      logger.error('Error during graceful shutdown:', error);
      process.exit(1);
    }
  }
}

// Start the service
const deviceService = new DeviceService();
deviceService.start().catch((error) => {
  logger.error('Failed to start Device Service:', error);
  process.exit(1);
}); 