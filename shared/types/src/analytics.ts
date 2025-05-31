import { Timestamp } from './common';

export enum MetricType {
  ENERGY = 'energy',
  POWER = 'power',
  EFFICIENCY = 'efficiency',
  FINANCIAL = 'financial',
  PERFORMANCE = 'performance'
}

export enum AggregationType {
  SUM = 'sum',
  AVERAGE = 'average',
  MIN = 'min',
  MAX = 'max',
  COUNT = 'count'
}

export enum TimeInterval {
  MINUTE = 'minute',
  HOUR = 'hour',
  DAY = 'day',
  WEEK = 'week',
  MONTH = 'month',
  YEAR = 'year'
}

export interface MetricDefinition {
  id: string;
  name: string;
  type: MetricType;
  unit: string;
  description?: string;
  aggregation: AggregationType;
  formula?: string;
}

export interface DataPoint {
  timestamp: Timestamp;
  value: number;
  metadata?: Record<string, any>;
}

export interface TimeSeries {
  metric: string;
  deviceId?: string;
  interval: TimeInterval;
  data: DataPoint[];
  aggregation: AggregationType;
  period: {
    start: Timestamp;
    end: Timestamp;
  };
}

export interface Report {
  id: string;
  name: string;
  type: ReportType;
  deviceIds: string[];
  period: {
    start: Timestamp;
    end: Timestamp;
  };
  metrics: string[];
  data: TimeSeries[];
  summary: ReportSummary;
  generatedAt: Timestamp;
  createdBy: string;
}

export enum ReportType {
  ENERGY_CONSUMPTION = 'energy_consumption',
  TRADING_PERFORMANCE = 'trading_performance',
  DEVICE_HEALTH = 'device_health',
  FINANCIAL_SUMMARY = 'financial_summary',
  EFFICIENCY_ANALYSIS = 'efficiency_analysis'
}

export interface ReportSummary {
  totalEnergy: number; // kWh
  totalProfit: number; // €
  averageEfficiency: number; // %
  peakPower: number; // kW
  uptime: number; // %
  keyInsights: string[];
  recommendations: string[];
}

export interface Alert {
  id: string;
  deviceId?: string;
  type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  threshold?: {
    metric: string;
    operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
    value: number;
  };
  status: AlertStatus;
  triggeredAt: Timestamp;
  acknowledgedAt?: Timestamp;
  resolvedAt?: Timestamp;
  acknowledgedBy?: string;
}

export enum AlertType {
  DEVICE_OFFLINE = 'device_offline',
  LOW_BATTERY = 'low_battery',
  HIGH_TEMPERATURE = 'high_temperature',
  TRADING_LOSS = 'trading_loss',
  EFFICIENCY_DROP = 'efficiency_drop',
  GRID_FAULT = 'grid_fault',
  MAINTENANCE_DUE = 'maintenance_due'
}

export enum AlertSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum AlertStatus {
  ACTIVE = 'active',
  ACKNOWLEDGED = 'acknowledged',
  RESOLVED = 'resolved',
  SUPPRESSED = 'suppressed'
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  widgets: DashboardWidget[];
  layout: DashboardLayout;
  isPublic: boolean;
  createdBy: string;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

export interface DashboardWidget {
  id: string;
  type: WidgetType;
  title: string;
  config: WidgetConfig;
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export enum WidgetType {
  LINE_CHART = 'line_chart',
  BAR_CHART = 'bar_chart',
  PIE_CHART = 'pie_chart',
  GAUGE = 'gauge',
  KPI = 'kpi',
  TABLE = 'table',
  MAP = 'map'
}

export interface WidgetConfig {
  metrics: string[];
  deviceIds?: string[];
  timeRange: {
    start: Timestamp;
    end: Timestamp;
  };
  refreshInterval?: number; // seconds
  thresholds?: Array<{
    value: number;
    color: string;
    label?: string;
  }>;
  displayOptions?: Record<string, any>;
}

export interface DashboardLayout {
  columns: number;
  rows: number;
  gridSize: number;
} 