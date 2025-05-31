import { Timestamp } from './common';

export enum DeviceType {
  INVERTER = 'inverter',
  BATTERY = 'battery'
}

export enum DeviceStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  ERROR = 'error',
  MAINTENANCE = 'maintenance'
}

export enum BatteryState {
  CHARGING = 'charging',
  DISCHARGING = 'discharging',
  IDLE = 'idle',
  FAULT = 'fault'
}

export enum InverterMode {
  GRID_TIE = 'grid_tie',
  OFF_GRID = 'off_grid',
  HYBRID = 'hybrid',
  STANDBY = 'standby'
}

export interface Device {
  id: string;
  name: string;
  type: DeviceType;
  status: DeviceStatus;
  location?: string;
  serialNumber?: string;
  model?: string;
  manufacturer?: string;
  firmwareVersion?: string;
  lastSeen: Timestamp;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

export interface BatteryData {
  deviceId: string;
  timestamp: Timestamp;
  stateOfCharge: number; // 0-100%
  voltage: number; // V
  current: number; // A
  power: number; // W
  temperature: number; // °C
  state: BatteryState;
  capacity: number; // Ah
  cycleCount: number;
  health: number; // 0-100%
}

export interface InverterData {
  deviceId: string;
  timestamp: Timestamp;
  mode: InverterMode;
  gridVoltage: number; // V
  gridCurrent: number; // A
  gridPower: number; // W
  gridFrequency: number; // Hz
  loadVoltage: number; // V
  loadCurrent: number; // A
  loadPower: number; // W
  pvVoltage: number; // V
  pvCurrent: number; // A
  pvPower: number; // W
  batteryVoltage: number; // V
  batteryCurrent: number; // A
  batteryPower: number; // W
  temperature: number; // °C
  efficiency: number; // 0-100%
}

export interface DeviceCommand {
  id: string;
  deviceId: string;
  command: string;
  parameters?: Record<string, any>;
  priority: CommandPriority;
  status: CommandStatus;
  createdAt: Timestamp;
  executedAt?: Timestamp;
  completedAt?: Timestamp;
  error?: string;
}

export enum CommandPriority {
  EMERGENCY = 'emergency',
  CRITICAL = 'critical',
  NORMAL = 'normal',
  LOW = 'low'
}

export enum CommandStatus {
  PENDING = 'pending',
  EXECUTING = 'executing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface ModbusRegister {
  address: number;
  name: string;
  type: 'holding' | 'input' | 'coil' | 'discrete';
  dataType: 'uint16' | 'int16' | 'uint32' | 'int32' | 'float32' | 'bool';
  scale?: number;
  unit?: string;
  description?: string;
  writable: boolean;
} 