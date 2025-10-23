/**
 * Inbound Forecast Feature
 * 受入予測データの取得と表示
 */

// Ports
export type { IInboundForecastRepository } from "./ports/repository";

// Infrastructure
export { HttpInboundForecastRepository } from "./infrastructure/inboundForecast.repository";
export { MockInboundForecastRepository } from "./infrastructure/inboundForecast.mock.repository";

// Application
export {
  useInboundForecastVM,
  useUkeireForecastVM,
  type InboundForecastViewModel,
  type UkeireForecastViewModel,
} from "./application/useInboundForecastVM";

// UI
export { ForecastCard, type ForecastCardProps, type KPIBlockProps } from "./ui/cards/ForecastCard";
