/**
 * Health check routes for Device Service
 */

import { Router } from 'express';

const router = Router();

// Basic health check
router.get('/', (req, res) => {
  res.json({
    service: 'device-service',
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0'
  });
});

// Detailed health check
router.get('/detailed', async (req, res) => {
  try {
    // TODO: Add detailed health checks for databases, MQTT, etc.
    res.json({
      service: 'device-service',
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      components: {
        database: { status: 'healthy' },
        mqtt: { status: 'healthy' },
        redis: { status: 'healthy' }
      }
    });
  } catch (error) {
    res.status(503).json({
      service: 'device-service',
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: (error as Error).message
    });
  }
});

export default router; 