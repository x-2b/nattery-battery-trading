import { Timestamp } from './common';

export enum TradingStrategy {
  PEAK_SHAVING = 'peak_shaving',
  ARBITRAGE = 'arbitrage',
  GRID_SUPPORT = 'grid_support',
  MANUAL = 'manual'
}

export enum TradingAction {
  BUY = 'buy',
  SELL = 'sell',
  HOLD = 'hold'
}

export enum OrderStatus {
  PENDING = 'pending',
  ACTIVE = 'active',
  EXECUTED = 'executed',
  CANCELLED = 'cancelled',
  FAILED = 'failed'
}

export interface EnergyPrice {
  timestamp: Timestamp;
  price: number; // €/MWh
  currency: string;
  market: string;
  validFrom: Timestamp;
  validTo: Timestamp;
}

export interface TradingOrder {
  id: string;
  deviceId: string;
  strategy: TradingStrategy;
  action: TradingAction;
  quantity: number; // kWh
  targetPrice?: number; // €/MWh
  maxPrice?: number; // €/MWh
  minPrice?: number; // €/MWh
  status: OrderStatus;
  scheduledAt: Timestamp;
  executedAt?: Timestamp;
  completedAt?: Timestamp;
  actualPrice?: number;
  actualQuantity?: number;
  profit?: number;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

export interface TradingSession {
  id: string;
  deviceId: string;
  strategy: TradingStrategy;
  startTime: Timestamp;
  endTime?: Timestamp;
  totalProfit: number;
  totalEnergy: number; // kWh
  orders: TradingOrder[];
  status: 'active' | 'completed' | 'cancelled';
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

export interface PriceOptimization {
  deviceId: string;
  timestamp: Timestamp;
  currentPrice: number;
  predictedPrices: Array<{
    timestamp: Timestamp;
    price: number;
    confidence: number; // 0-1
  }>;
  recommendation: {
    action: TradingAction;
    quantity: number;
    expectedProfit: number;
    confidence: number;
    reasoning: string;
  };
}

export interface MarketData {
  timestamp: Timestamp;
  dayAheadPrices: EnergyPrice[];
  intradayPrices: EnergyPrice[];
  gridLoad: number; // MW
  renewableGeneration: number; // MW
  demandForecast: Array<{
    timestamp: Timestamp;
    demand: number; // MW
  }>;
}

export interface TradingMetrics {
  deviceId: string;
  period: {
    start: Timestamp;
    end: Timestamp;
  };
  totalProfit: number;
  totalLoss: number;
  netProfit: number;
  totalEnergy: number; // kWh
  averagePrice: number; // €/MWh
  successfulTrades: number;
  failedTrades: number;
  successRate: number; // 0-100%
  roi: number; // Return on Investment %
} 