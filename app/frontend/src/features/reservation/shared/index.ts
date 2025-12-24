/**
 * Public API for shared reservation repository
 * 
 * 規約: 共通Repository層、複数featureから利用可能
 */

// Repository Interface (Port)
export type {
  ReservationDailyRepository,
  ReservationForecastDaily,
  ReservationManualInput,
} from './ports/ReservationDailyRepository';

// Repository Implementations (Infrastructure)
export { ReservationDailyHttpRepository, reservationDailyRepository } from './infrastructure/ReservationDailyHttpRepository';
export { ReservationDailyMockRepository, reservationDailyMockRepository } from './infrastructure/ReservationDailyMockRepository';
