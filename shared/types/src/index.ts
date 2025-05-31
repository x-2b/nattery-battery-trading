// Device and Hardware Types
export interface BatteryStatus {
  id: string;
  timestamp: Date;
  stateOfCharge: number; // 0-100%
  voltage: number; // Volts
  current: number; // Amperes (positive = charging, negative = discharging)
  power: number; // Watts
  temperature: number; // Celsius
  health: number; // 0-100%
  cycleCount: number;
  capacity: {
    current: number; // Ah
    design: number; // Ah
  };
  status: 'charging' | 'discharging' | 'idle' | 'fault';
}

export interface InverterStatus {
  id: string;
  timestamp: Date;
  acVoltage: number;
  acCurrent: number;
  acPower: number;
  dcVoltage: number;
  dcCurrent: number;
  dcPower: number;
  frequency: number;
  efficiency: number;
  temperature: number;
  status: 'online' | 'offline' | 'fault' | 'maintenance';
  faultCodes: string[];
}

export interface ModbusDevice {
  id: string;
  name: string;
  address: number;
  type: 'battery' | 'inverter' | 'meter' | 'sensor';
  connectionStatus: 'connected' | 'disconnected' | 'error';
  lastSeen: Date;
  registers: ModbusRegister[];
}

export interface ModbusRegister {
  address: number;
  type: 'holding' | 'input' | 'coil' | 'discrete';
  value: number | boolean;
  unit?: string;
  description: string;
}

// Trading Types
export interface EnergyPrice {
  timestamp: Date;
  price: number; // $/kWh
  currency: string;
  market: string;
  type: 'spot' | 'day_ahead' | 'real_time';
}

export interface TradingStrategy {
  id: string;
  name: string;
  type: 'peak_shaving' | 'arbitrage' | 'grid_services' | 'custom';
  enabled: boolean;
  parameters: Record<string, any>;
  constraints: {
    minSoC: number; // Minimum state of charge %
    maxSoC: number; // Maximum state of charge %
    maxPower: number; // Maximum power in kW
    timeWindows: TimeWindow[];
  };
  performance: {
    totalSavings: number;
    totalTrades: number;
    successRate: number;
    lastExecuted?: Date;
  };
}

export interface TimeWindow {
  start: string; // HH:MM format
  end: string; // HH:MM format
  days: ('monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday')[];
}

export interface TradingOrder {
  id: string;
  timestamp: Date;
  type: 'charge' | 'discharge';
  power: number; // kW (positive = charge, negative = discharge)
  duration: number; // minutes
  targetSoC?: number; // Target state of charge %
  price: number; // $/kWh
  strategy: string;
  status: 'pending' | 'executing' | 'completed' | 'cancelled' | 'failed';
  executedAt?: Date;
  completedAt?: Date;
  actualEnergy?: number; // kWh
  actualCost?: number; // $
}

// Analytics Types
export interface EnergyMetrics {
  timestamp: Date;
  consumption: number; // kWh
  production: number; // kWh (solar, wind, etc.)
  gridImport: number; // kWh
  gridExport: number; // kWh
  batteryCharge: number; // kWh
  batteryDischarge: number; // kWh
  cost: number; // $
  savings: number; // $
}

export interface PerformanceReport {
  period: {
    start: Date;
    end: Date;
  };
  summary: {
    totalEnergy: number; // kWh
    totalCost: number; // $
    totalSavings: number; // $
    averageEfficiency: number; // %
    peakDemandReduction: number; // kW
  };
  breakdown: {
    byStrategy: Record<string, PerformanceMetrics>;
    byTimeOfDay: Record<string, PerformanceMetrics>;
    byDay: Record<string, PerformanceMetrics>;
  };
}

export interface PerformanceMetrics {
  energy: number; // kWh
  cost: number; // $
  savings: number; // $
  trades: number;
  efficiency: number; // %
}

// User and Authentication Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'viewer';
  preferences: UserPreferences;
  createdAt: Date;
  lastLogin?: Date;
}

export interface UserPreferences {
  timezone: string;
  currency: string;
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
    alerts: NotificationAlert[];
  };
  dashboard: {
    defaultView: 'overview' | 'trading' | 'analytics';
    refreshInterval: number; // seconds
    charts: string[];
  };
}

export interface NotificationAlert {
  type: 'battery_low' | 'battery_high' | 'system_fault' | 'trading_opportunity' | 'high_savings';
  threshold: number;
  enabled: boolean;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: Date;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// WebSocket Event Types
export interface WebSocketEvent {
  type: string;
  payload: any;
  timestamp: Date;
}

export interface DeviceUpdateEvent extends WebSocketEvent {
  type: 'device_update';
  payload: {
    deviceId: string;
    status: BatteryStatus | InverterStatus;
  };
}

export interface TradingUpdateEvent extends WebSocketEvent {
  type: 'trading_update';
  payload: {
    orderId: string;
    status: TradingOrder['status'];
    progress?: number;
  };
}

export interface AlertEvent extends WebSocketEvent {
  type: 'alert';
  payload: {
    level: 'info' | 'warning' | 'error' | 'critical';
    title: string;
    message: string;
    source: string;
    deviceId?: string;
  };
}

// Configuration Types
export interface SystemConfig {
  devices: {
    battery: {
      capacity: number; // kWh
      maxPower: number; // kW
      efficiency: number; // %
      minSoC: number; // %
      maxSoC: number; // %
    };
    inverter: {
      maxPower: number; // kW
      efficiency: number; // %
    };
    modbus: {
      host: string;
      port: number;
      timeout: number;
      retries: number;
    };
  };
  trading: {
    enabled: boolean;
    defaultStrategy: string;
    riskLevel: 'low' | 'medium' | 'high';
    maxDailyTrades: number;
    emergencyStopSoC: number; // %
  };
  monitoring: {
    dataRetention: number; // days
    alertThresholds: Record<string, number>;
    reportingInterval: number; // minutes
  };
}

// Error Types
export class NatteryError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public details?: any
  ) {
    super(message);
    this.name = 'NatteryError';
  }
}

export class DeviceError extends NatteryError {
  constructor(message: string, deviceId: string, details?: any) {
    super(message, 'DEVICE_ERROR', 500, { deviceId, ...details });
    this.name = 'DeviceError';
  }
}

export class TradingError extends NatteryError {
  constructor(message: string, orderId?: string, details?: any) {
    super(message, 'TRADING_ERROR', 400, { orderId, ...details });
    this.name = 'TradingError';
  }
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Timestamp = string | Date | number;

export type SortOrder = 'asc' | 'desc';

export interface QueryOptions {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: SortOrder;
  filters?: Record<string, any>;
  search?: string;
}

export interface TimeRange {
  start: Timestamp;
  end: Timestamp;
}

// Core types
export * from './device';
export * from './trading';
export * from './analytics';
export * from './user';
export * from './common';

// Validation schemas
export * from './schemas'; 