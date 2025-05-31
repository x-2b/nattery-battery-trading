/**
 * MQTT Manager for Device Service
 * 
 * Handles MQTT communication with Edge Bridge Service.
 * Subscribes to device data, status, and alert topics.
 * Publishes commands and receives responses.
 */

import mqtt, { MqttClient } from 'mqtt';
import { config } from '../config/config';
import { logger, logMQTTMessage, logError } from '../utils/logger';
import { DeviceManager } from '../services/DeviceManager';
import { DataProcessor } from '../services/DataProcessor';
import { CommandManager } from '../services/CommandManager';
import { WebSocketManager } from '../websocket/WebSocketManager';

export interface MQTTMessage {
  topic: string;
  payload: any;
  timestamp: string;
}

export interface DeviceDataMessage {
  device_id: string;
  device_type: string;
  timestamp: string;
  data: Record<string, any>;
}

export interface DeviceStatusMessage {
  device_id: string;
  device_type: string;
  timestamp: string;
  status: string;
  [key: string]: any;
}

export interface DeviceAlertMessage {
  device_id: string;
  device_type: string;
  timestamp: string;
  alert_type: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

export interface CommandResponseMessage {
  device_id: string;
  command_id: string;
  timestamp: string;
  success: boolean;
  result?: any;
  error?: string;
}

export class MQTTManager {
  private client: MqttClient | null = null;
  private connected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectInterval = 5000; // 5 seconds

  constructor(
    private deviceManager: DeviceManager,
    private dataProcessor: DataProcessor,
    private commandManager: CommandManager,
    private webSocketManager: WebSocketManager
  ) {}

  public async connect(): Promise<void> {
    try {
      logger.info('Connecting to MQTT broker...', {
        broker: config.mqtt.brokerUrl,
        clientId: config.mqtt.clientId
      });

      const options: mqtt.IClientOptions = {
        clientId: config.mqtt.clientId,
        clean: true,
        connectTimeout: 30000,
        reconnectPeriod: this.reconnectInterval,
        keepalive: 60,
      };

      // Add authentication if configured
      if (config.mqtt.username && config.mqtt.password) {
        options.username = config.mqtt.username;
        options.password = config.mqtt.password;
      }

      this.client = mqtt.connect(config.mqtt.brokerUrl, options);

      // Set up event handlers
      this.setupEventHandlers();

      // Wait for connection
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('MQTT connection timeout'));
        }, 30000);

        this.client!.on('connect', () => {
          clearTimeout(timeout);
          this.connected = true;
          this.reconnectAttempts = 0;
          logger.info('Connected to MQTT broker');
          this.subscribeToTopics();
          resolve();
        });

        this.client!.on('error', (error) => {
          clearTimeout(timeout);
          reject(error);
        });
      });

    } catch (error) {
      logError(error as Error, 'MQTT connection');
      throw error;
    }
  }

  public async disconnect(): Promise<void> {
    if (this.client && this.connected) {
      logger.info('Disconnecting from MQTT broker...');
      
      return new Promise((resolve) => {
        this.client!.end(false, {}, () => {
          this.connected = false;
          logger.info('Disconnected from MQTT broker');
          resolve();
        });
      });
    }
  }

  public isConnected(): boolean {
    return this.connected && this.client?.connected === true;
  }

  private setupEventHandlers(): void {
    if (!this.client) return;

    this.client.on('connect', () => {
      this.connected = true;
      this.reconnectAttempts = 0;
      logger.info('MQTT connected');
    });

    this.client.on('disconnect', () => {
      this.connected = false;
      logger.warn('MQTT disconnected');
    });

    this.client.on('reconnect', () => {
      this.reconnectAttempts++;
      logger.info(`MQTT reconnecting... (attempt ${this.reconnectAttempts})`);
    });

    this.client.on('error', (error) => {
      logError(error, 'MQTT client error');
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        logger.error('Max MQTT reconnect attempts reached');
        this.client?.end();
      }
    });

    this.client.on('message', async (topic, payload) => {
      try {
        await this.handleMessage(topic, payload);
      } catch (error) {
        logError(error as Error, 'MQTT message handling', { topic });
      }
    });
  }

  private async subscribeToTopics(): Promise<void> {
    if (!this.client || !this.connected) return;

    const topics = [
      `${config.mqtt.topics.prefix}/+/${config.mqtt.topics.data}`,
      `${config.mqtt.topics.prefix}/+/${config.mqtt.topics.status}`,
      `${config.mqtt.topics.prefix}/+/${config.mqtt.topics.alerts}`,
      `${config.mqtt.topics.prefix}/+/${config.mqtt.topics.commands}/response`,
    ];

    for (const topic of topics) {
      try {
        await new Promise<void>((resolve, reject) => {
          this.client!.subscribe(topic, { qos: 1 }, (error) => {
            if (error) {
              reject(error);
            } else {
              logger.info(`Subscribed to MQTT topic: ${topic}`);
              resolve();
            }
          });
        });
      } catch (error) {
        logError(error as Error, 'MQTT subscription', { topic });
      }
    }
  }

  private async handleMessage(topic: string, payload: Buffer): Promise<void> {
    try {
      const message = JSON.parse(payload.toString());
      const topicParts = topic.split('/');
      
      if (topicParts.length < 3) {
        logger.warn('Invalid MQTT topic format', { topic });
        return;
      }

      const deviceId = topicParts[1];
      const messageType = topicParts[2];

      logMQTTMessage(topic, 'receive', { deviceId, messageType });

      switch (messageType) {
        case config.mqtt.topics.data:
          await this.handleDeviceData(message as DeviceDataMessage);
          break;

        case config.mqtt.topics.status:
          await this.handleDeviceStatus(message as DeviceStatusMessage);
          break;

        case config.mqtt.topics.alerts:
          await this.handleDeviceAlert(message as DeviceAlertMessage);
          break;

        case config.mqtt.topics.commands:
          if (topicParts[3] === 'response') {
            await this.handleCommandResponse(message as CommandResponseMessage);
          }
          break;

        default:
          logger.warn('Unknown MQTT message type', { topic, messageType });
      }

    } catch (error) {
      logError(error as Error, 'MQTT message parsing', { topic });
    }
  }

  private async handleDeviceData(message: DeviceDataMessage): Promise<void> {
    try {
      logger.debug('Processing device data', {
        deviceId: message.device_id,
        dataKeys: Object.keys(message.data)
      });

      // Ensure device is registered
      await this.deviceManager.ensureDeviceRegistered({
        deviceId: message.device_id,
        deviceType: message.device_type,
        lastSeen: new Date(message.timestamp)
      });

      // Process the data
      await this.dataProcessor.processDeviceData(message);

      // Broadcast to WebSocket clients
      this.webSocketManager.broadcastDeviceData(message.device_id, message.data);

    } catch (error) {
      logError(error as Error, 'Device data processing', {
        deviceId: message.device_id
      });
    }
  }

  private async handleDeviceStatus(message: DeviceStatusMessage): Promise<void> {
    try {
      logger.debug('Processing device status', {
        deviceId: message.device_id,
        status: message.status
      });

      // Update device status
      await this.deviceManager.updateDeviceStatus({
        deviceId: message.device_id,
        status: message.status,
        lastSeen: new Date(message.timestamp),
        metadata: message
      });

      // Broadcast to WebSocket clients
      this.webSocketManager.broadcastDeviceStatus(message.device_id, message);

    } catch (error) {
      logError(error as Error, 'Device status processing', {
        deviceId: message.device_id
      });
    }
  }

  private async handleDeviceAlert(message: DeviceAlertMessage): Promise<void> {
    try {
      logger.info('Processing device alert', {
        deviceId: message.device_id,
        alertType: message.alert_type,
        severity: message.severity
      });

      // Store alert
      await this.dataProcessor.processDeviceAlert(message);

      // Broadcast to WebSocket clients
      this.webSocketManager.broadcastDeviceAlert(message.device_id, message);

      // Handle critical alerts
      if (message.severity === 'critical') {
        logger.error('Critical device alert received', {
          deviceId: message.device_id,
          message: message.message
        });
        
        // TODO: Trigger emergency procedures if needed
      }

    } catch (error) {
      logError(error as Error, 'Device alert processing', {
        deviceId: message.device_id
      });
    }
  }

  private async handleCommandResponse(message: CommandResponseMessage): Promise<void> {
    try {
      logger.debug('Processing command response', {
        deviceId: message.device_id,
        commandId: message.command_id,
        success: message.success
      });

      // Update command status
      await this.commandManager.updateCommandStatus(
        message.command_id,
        message.success ? 'completed' : 'failed',
        message.result,
        message.error
      );

      // Broadcast to WebSocket clients
      this.webSocketManager.broadcastCommandResponse(message.device_id, message);

    } catch (error) {
      logError(error as Error, 'Command response processing', {
        commandId: message.command_id
      });
    }
  }

  public async publishCommand(deviceId: string, command: any): Promise<void> {
    if (!this.client || !this.connected) {
      throw new Error('MQTT client not connected');
    }

    const topic = `${config.mqtt.topics.prefix}/${deviceId}/${config.mqtt.topics.commands}`;
    const payload = JSON.stringify(command);

    return new Promise((resolve, reject) => {
      this.client!.publish(topic, payload, { qos: 1 }, (error) => {
        if (error) {
          logError(error, 'MQTT command publish', { deviceId, topic });
          reject(error);
        } else {
          logMQTTMessage(topic, 'publish', { deviceId, commandId: command.command_id });
          resolve();
        }
      });
    });
  }

  public getConnectionStatus(): any {
    return {
      connected: this.connected,
      reconnectAttempts: this.reconnectAttempts,
      brokerUrl: config.mqtt.brokerUrl,
      clientId: config.mqtt.clientId
    };
  }
} 