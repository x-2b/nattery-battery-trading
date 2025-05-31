/**
 * Database Manager for Device Service
 * 
 * Manages connections to PostgreSQL (transactional data) and InfluxDB (time-series data).
 * Provides unified interface for database operations.
 */

import { PrismaClient } from '@prisma/client';
import { InfluxDB, Point, WriteApi, QueryApi } from '@influxdata/influxdb-client';
import { config } from '../config/config';
import { logger, logDatabaseQuery, logError } from '../utils/logger';

export interface DatabaseHealth {
  postgres: {
    connected: boolean;
    latency?: number;
    error?: string;
  };
  influxdb: {
    connected: boolean;
    latency?: number;
    error?: string;
  };
}

export class DatabaseManager {
  private prisma: PrismaClient | null = null;
  private influxDB: InfluxDB | null = null;
  private influxWriteApi: WriteApi | null = null;
  private influxQueryApi: QueryApi | null = null;

  public async initialize(): Promise<void> {
    try {
      logger.info('Initializing database connections...');

      // Initialize PostgreSQL connection
      await this.initializePostgreSQL();
      
      // Initialize InfluxDB connection
      await this.initializeInfluxDB();

      logger.info('Database connections initialized successfully');

    } catch (error) {
      logError(error as Error, 'Database initialization');
      throw error;
    }
  }

  private async initializePostgreSQL(): Promise<void> {
    try {
      this.prisma = new PrismaClient({
        log: [
          { level: 'query', emit: 'event' },
          { level: 'error', emit: 'event' },
          { level: 'warn', emit: 'event' },
        ],
        datasources: {
          db: {
            url: config.databaseUrl,
          },
        },
      });

      // Set up logging
      this.prisma.$on('query', (e) => {
        logDatabaseQuery(e.query, e.duration, {
          params: e.params,
          target: e.target,
        });
      });

      this.prisma.$on('error', (e) => {
        logError(new Error(e.message), 'Prisma error', {
          target: e.target,
          timestamp: e.timestamp,
        });
      });

      this.prisma.$on('warn', (e) => {
        logger.warn('Prisma warning', {
          message: e.message,
          target: e.target,
          timestamp: e.timestamp,
        });
      });

      // Test connection
      await this.prisma.$connect();
      logger.info('PostgreSQL connection established');

    } catch (error) {
      logError(error as Error, 'PostgreSQL initialization');
      throw error;
    }
  }

  private async initializeInfluxDB(): Promise<void> {
    try {
      this.influxDB = new InfluxDB({
        url: config.influxdb.url,
        token: config.influxdb.token,
      });

      // Create write and query APIs
      this.influxWriteApi = this.influxDB.getWriteApi(
        config.influxdb.org,
        config.influxdb.bucket,
        'ms' // precision
      );

      this.influxQueryApi = this.influxDB.getQueryApi(config.influxdb.org);

      // Test connection by performing a simple query
      const testQuery = `
        from(bucket: "${config.influxdb.bucket}")
        |> range(start: -1m)
        |> limit(n: 1)
      `;

      await this.influxQueryApi.collectRows(testQuery);
      logger.info('InfluxDB connection established');

    } catch (error) {
      logError(error as Error, 'InfluxDB initialization');
      throw error;
    }
  }

  public async close(): Promise<void> {
    try {
      logger.info('Closing database connections...');

      // Close PostgreSQL connection
      if (this.prisma) {
        await this.prisma.$disconnect();
        this.prisma = null;
        logger.info('PostgreSQL connection closed');
      }

      // Close InfluxDB connection
      if (this.influxWriteApi) {
        await this.influxWriteApi.close();
        this.influxWriteApi = null;
        this.influxQueryApi = null;
        this.influxDB = null;
        logger.info('InfluxDB connection closed');
      }

    } catch (error) {
      logError(error as Error, 'Database cleanup');
    }
  }

  // PostgreSQL operations
  public getPrisma(): PrismaClient {
    if (!this.prisma) {
      throw new Error('PostgreSQL not initialized');
    }
    return this.prisma;
  }

  public async executeTransaction<T>(
    operation: (prisma: PrismaClient) => Promise<T>
  ): Promise<T> {
    if (!this.prisma) {
      throw new Error('PostgreSQL not initialized');
    }

    return this.prisma.$transaction(operation);
  }

  // InfluxDB operations
  public getInfluxWriteApi(): WriteApi {
    if (!this.influxWriteApi) {
      throw new Error('InfluxDB write API not initialized');
    }
    return this.influxWriteApi;
  }

  public getInfluxQueryApi(): QueryApi {
    if (!this.influxQueryApi) {
      throw new Error('InfluxDB query API not initialized');
    }
    return this.influxQueryApi;
  }

  public createInfluxPoint(measurement: string): Point {
    return new Point(measurement);
  }

  public async writeInfluxPoints(points: Point[]): Promise<void> {
    if (!this.influxWriteApi) {
      throw new Error('InfluxDB write API not initialized');
    }

    try {
      this.influxWriteApi.writePoints(points);
      await this.influxWriteApi.flush();
    } catch (error) {
      logError(error as Error, 'InfluxDB write operation');
      throw error;
    }
  }

  public async queryInfluxData(query: string): Promise<any[]> {
    if (!this.influxQueryApi) {
      throw new Error('InfluxDB query API not initialized');
    }

    try {
      const startTime = Date.now();
      const result = await this.influxQueryApi.collectRows(query);
      const duration = Date.now() - startTime;
      
      logDatabaseQuery(query, duration, {
        database: 'influxdb',
        rowCount: result.length,
      });

      return result;
    } catch (error) {
      logError(error as Error, 'InfluxDB query operation', { query });
      throw error;
    }
  }

  // Health check methods
  public async checkHealth(): Promise<DatabaseHealth> {
    const health: DatabaseHealth = {
      postgres: { connected: false },
      influxdb: { connected: false },
    };

    // Check PostgreSQL
    try {
      const startTime = Date.now();
      await this.prisma?.$queryRaw`SELECT 1`;
      health.postgres.connected = true;
      health.postgres.latency = Date.now() - startTime;
    } catch (error) {
      health.postgres.error = (error as Error).message;
      logError(error as Error, 'PostgreSQL health check');
    }

    // Check InfluxDB
    try {
      const startTime = Date.now();
      const testQuery = `
        from(bucket: "${config.influxdb.bucket}")
        |> range(start: -1m)
        |> limit(n: 1)
      `;
      await this.influxQueryApi?.collectRows(testQuery);
      health.influxdb.connected = true;
      health.influxdb.latency = Date.now() - startTime;
    } catch (error) {
      health.influxdb.error = (error as Error).message;
      logError(error as Error, 'InfluxDB health check');
    }

    return health;
  }

  // Utility methods
  public async getPostgreSQLVersion(): Promise<string> {
    if (!this.prisma) {
      throw new Error('PostgreSQL not initialized');
    }

    const result = await this.prisma.$queryRaw<[{ version: string }]>`SELECT version()`;
    return result[0]?.version || 'Unknown';
  }

  public async getInfluxDBHealth(): Promise<any> {
    if (!this.influxDB) {
      throw new Error('InfluxDB not initialized');
    }

    try {
      const healthApi = this.influxDB.getHealthApi();
      return await healthApi.getHealth();
    } catch (error) {
      logError(error as Error, 'InfluxDB health API');
      throw error;
    }
  }

  // Data retention management
  public async cleanupOldData(retentionDays: number): Promise<void> {
    try {
      logger.info(`Starting data cleanup for records older than ${retentionDays} days`);

      // Clean up PostgreSQL data
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

      if (this.prisma) {
        // Example: Clean up old device events
        const deletedEvents = await this.prisma.deviceEvent.deleteMany({
          where: {
            createdAt: {
              lt: cutoffDate,
            },
          },
        });

        logger.info(`Cleaned up ${deletedEvents.count} old device events from PostgreSQL`);
      }

      // InfluxDB retention is typically handled by retention policies
      // but we can also delete old data manually if needed
      if (this.influxQueryApi) {
        const deleteQuery = `
          from(bucket: "${config.influxdb.bucket}")
          |> range(start: -${retentionDays}d, stop: -${retentionDays}d)
          |> drop()
        `;

        // Note: This is a simplified example. In practice, you'd use the delete API
        logger.info('InfluxDB cleanup would be handled by retention policies');
      }

    } catch (error) {
      logError(error as Error, 'Data cleanup operation');
      throw error;
    }
  }
} 