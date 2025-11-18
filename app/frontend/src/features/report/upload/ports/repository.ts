/**
 * Report Feature - Ports Layer
 */

// TODO: Define proper types when implementing repository pattern
export interface IReportRepository {
  fetchReports(): Promise<unknown[]>;
  generateReport(config: unknown): Promise<Blob>;
}
