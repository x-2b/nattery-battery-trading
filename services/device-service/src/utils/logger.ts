/**
 * Logger utility using Winston
 */

import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';

// Define log levels
const levels = {
  error: 0,
  warn: 1,
  info: 2,
  debug: 3,
};

// Define colors for console output
const colors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  debug: 'blue',
};

winston.addColors(colors);

// Get log level from environment
const logLevel = process.env.LOG_LEVEL || 'info';
const logFormat = process.env.LOG_FORMAT || 'json';
const nodeEnv = process.env.NODE_ENV || 'development';

// Create formatters
const consoleFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.colorize({ all: true }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    const metaStr = Object.keys(meta).length ? JSON.stringify(meta, null, 2) : '';
    return `${timestamp} [${level}]: ${message} ${metaStr}`;
  })
);

const jsonFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

const simpleFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    const metaStr = Object.keys(meta).length ? JSON.stringify(meta) : '';
    return `${timestamp} [${level.toUpperCase()}]: ${message} ${metaStr}`;
  })
);

// Create transports
const transports: winston.transport[] = [];

// Console transport (always enabled in development)
if (nodeEnv === 'development') {
  transports.push(
    new winston.transports.Console({
      level: logLevel,
      format: consoleFormat,
    })
  );
} else {
  transports.push(
    new winston.transports.Console({
      level: logLevel,
      format: logFormat === 'json' ? jsonFormat : simpleFormat,
    })
  );
}

// File transports for production
if (nodeEnv === 'production') {
  // Error log file
  transports.push(
    new DailyRotateFile({
      filename: 'logs/error-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      level: 'error',
      format: jsonFormat,
      maxSize: '20m',
      maxFiles: '14d',
      zippedArchive: true,
    })
  );

  // Combined log file
  transports.push(
    new DailyRotateFile({
      filename: 'logs/combined-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      format: jsonFormat,
      maxSize: '20m',
      maxFiles: '14d',
      zippedArchive: true,
    })
  );
}

// Create logger instance
export const logger = winston.createLogger({
  level: logLevel,
  levels,
  format: jsonFormat,
  defaultMeta: {
    service: 'device-service',
    environment: nodeEnv,
    timestamp: new Date().toISOString(),
  },
  transports,
  exitOnError: false,
});

// Handle uncaught exceptions and unhandled rejections
if (nodeEnv === 'production') {
  logger.exceptions.handle(
    new DailyRotateFile({
      filename: 'logs/exceptions-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      format: jsonFormat,
      maxSize: '20m',
      maxFiles: '14d',
      zippedArchive: true,
    })
  );

  logger.rejections.handle(
    new DailyRotateFile({
      filename: 'logs/rejections-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      format: jsonFormat,
      maxSize: '20m',
      maxFiles: '14d',
      zippedArchive: true,
    })
  );
}

// Add request ID to logs if available
export const addRequestId = (requestId: string) => {
  return logger.child({ requestId });
};

// Performance logging helper
export const logPerformance = (operation: string, startTime: number, metadata?: any) => {
  const duration = Date.now() - startTime;
  logger.info(`Performance: ${operation}`, {
    operation,
    duration: `${duration}ms`,
    ...metadata,
  });
};

// Database query logging helper
export const logDatabaseQuery = (query: string, duration: number, metadata?: any) => {
  logger.debug('Database query executed', {
    query: query.substring(0, 200), // Truncate long queries
    duration: `${duration}ms`,
    ...metadata,
  });
};

// MQTT message logging helper
export const logMQTTMessage = (topic: string, action: 'publish' | 'receive', metadata?: any) => {
  logger.debug(`MQTT ${action}`, {
    topic,
    action,
    ...metadata,
  });
};

// WebSocket event logging helper
export const logWebSocketEvent = (event: string, socketId: string, metadata?: any) => {
  logger.debug('WebSocket event', {
    event,
    socketId,
    ...metadata,
  });
};

// Error logging helper with context
export const logError = (error: Error, context?: string, metadata?: any) => {
  logger.error(`Error${context ? ` in ${context}` : ''}`, {
    error: {
      name: error.name,
      message: error.message,
      stack: error.stack,
    },
    context,
    ...metadata,
  });
};

// Health check logging helper
export const logHealthCheck = (component: string, status: 'healthy' | 'unhealthy', metadata?: any) => {
  const level = status === 'healthy' ? 'debug' : 'warn';
  logger[level](`Health check: ${component}`, {
    component,
    status,
    ...metadata,
  });
};

export default logger; 