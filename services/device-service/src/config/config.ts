/**
 * Configuration management for Device Service
 */

import { z } from 'zod';

// Configuration schema with validation
const configSchema = z.object({
  // Server configuration
  port: z.number().min(1000).max(65535).default(3001),
  nodeEnv: z.enum(['development', 'production', 'test']).default('development'),
  
  // Database configuration
  databaseUrl: z.string().url(),
  
  // InfluxDB configuration
  influxdb: z.object({
    url: z.string().url(),
    token: z.string(),
    org: z.string(),
    bucket: z.string(),
  }),
  
  // Redis configuration
  redis: z.object({
    url: z.string(),
    password: z.string().optional(),
    db: z.number().default(0),
  }),
  
  // RabbitMQ configuration
  rabbitmq: z.object({
    url: z.string(),
    exchange: z.string().default('nattery'),
    queues: z.object({
      commands: z.string().default('device.commands'),
      events: z.string().default('device.events'),
      alerts: z.string().default('device.alerts'),
    }),
  }),
  
  // MQTT configuration
  mqtt: z.object({
    brokerUrl: z.string(),
    username: z.string().optional(),
    password: z.string().optional(),
    clientId: z.string().default('device-service'),
    topics: z.object({
      prefix: z.string().default('nattery'),
      data: z.string().default('data'),
      status: z.string().default('status'),
      commands: z.string().default('commands'),
      alerts: z.string().default('alerts'),
    }),
  }),
  
  // CORS configuration
  cors: z.object({
    origin: z.union([z.string(), z.array(z.string())]).default('*'),
  }),
  
  // Rate limiting
  rateLimit: z.object({
    windowMs: z.number().default(15 * 60 * 1000), // 15 minutes
    maxRequests: z.number().default(100),
  }),
  
  // WebSocket configuration
  websocket: z.object({
    pingTimeout: z.number().default(60000),
    pingInterval: z.number().default(25000),
  }),
  
  // Logging configuration
  logging: z.object({
    level: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
    format: z.enum(['json', 'simple']).default('json'),
    maxFiles: z.number().default(14),
    maxSize: z.string().default('20m'),
  }),
  
  // Health monitoring
  health: z.object({
    checkInterval: z.number().default(30000), // 30 seconds
    timeout: z.number().default(5000), // 5 seconds
  }),
  
  // Data processing
  dataProcessing: z.object({
    batchSize: z.number().default(100),
    flushInterval: z.number().default(5000), // 5 seconds
    retentionDays: z.number().default(365),
  }),
});

type Config = z.infer<typeof configSchema>;

// Load and validate configuration
function loadConfig(): Config {
  const rawConfig = {
    // Server
    port: parseInt(process.env.PORT || '3001', 10),
    nodeEnv: process.env.NODE_ENV || 'development',
    
    // Database
    databaseUrl: process.env.DATABASE_URL || 'postgresql://nattery:password@localhost:5432/nattery',
    
    // InfluxDB
    influxdb: {
      url: process.env.INFLUXDB_URL || 'http://localhost:8086',
      token: process.env.INFLUXDB_TOKEN || 'your-influxdb-token',
      org: process.env.INFLUXDB_ORG || 'nattery',
      bucket: process.env.INFLUXDB_BUCKET || 'energy_data',
    },
    
    // Redis
    redis: {
      url: process.env.REDIS_URL || 'redis://localhost:6379',
      password: process.env.REDIS_PASSWORD,
      db: parseInt(process.env.REDIS_DB || '0', 10),
    },
    
    // RabbitMQ
    rabbitmq: {
      url: process.env.RABBITMQ_URL || 'amqp://nattery:password@localhost:5672',
      exchange: process.env.RABBITMQ_EXCHANGE || 'nattery',
      queues: {
        commands: process.env.RABBITMQ_QUEUE_COMMANDS || 'device.commands',
        events: process.env.RABBITMQ_QUEUE_EVENTS || 'device.events',
        alerts: process.env.RABBITMQ_QUEUE_ALERTS || 'device.alerts',
      },
    },
    
    // MQTT
    mqtt: {
      brokerUrl: process.env.MQTT_BROKER_URL || 'mqtt://localhost:1883',
      username: process.env.MQTT_USERNAME,
      password: process.env.MQTT_PASSWORD,
      clientId: process.env.MQTT_CLIENT_ID || 'device-service',
      topics: {
        prefix: process.env.MQTT_TOPIC_PREFIX || 'nattery',
        data: process.env.MQTT_TOPIC_DATA || 'data',
        status: process.env.MQTT_TOPIC_STATUS || 'status',
        commands: process.env.MQTT_TOPIC_COMMANDS || 'commands',
        alerts: process.env.MQTT_TOPIC_ALERTS || 'alerts',
      },
    },
    
    // CORS
    cors: {
      origin: process.env.CORS_ORIGIN || '*',
    },
    
    // Rate limiting
    rateLimit: {
      windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000', 10),
      maxRequests: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100', 10),
    },
    
    // WebSocket
    websocket: {
      pingTimeout: parseInt(process.env.WS_PING_TIMEOUT || '60000', 10),
      pingInterval: parseInt(process.env.WS_PING_INTERVAL || '25000', 10),
    },
    
    // Logging
    logging: {
      level: process.env.LOG_LEVEL || 'info',
      format: process.env.LOG_FORMAT || 'json',
      maxFiles: parseInt(process.env.LOG_MAX_FILES || '14', 10),
      maxSize: process.env.LOG_MAX_SIZE || '20m',
    },
    
    // Health monitoring
    health: {
      checkInterval: parseInt(process.env.HEALTH_CHECK_INTERVAL || '30000', 10),
      timeout: parseInt(process.env.HEALTH_TIMEOUT || '5000', 10),
    },
    
    // Data processing
    dataProcessing: {
      batchSize: parseInt(process.env.DATA_BATCH_SIZE || '100', 10),
      flushInterval: parseInt(process.env.DATA_FLUSH_INTERVAL || '5000', 10),
      retentionDays: parseInt(process.env.DATA_RETENTION_DAYS || '365', 10),
    },
  };

  try {
    return configSchema.parse(rawConfig);
  } catch (error) {
    console.error('Configuration validation failed:', error);
    process.exit(1);
  }
}

export const config = loadConfig();

// Helper functions
export const isDevelopment = () => config.nodeEnv === 'development';
export const isProduction = () => config.nodeEnv === 'production';
export const isTest = () => config.nodeEnv === 'test'; 