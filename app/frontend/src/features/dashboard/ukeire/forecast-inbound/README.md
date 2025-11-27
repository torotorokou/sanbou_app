# Inbound Forecast Feature

受入予測データを取得して表示する機能。

## 公開API

- **VM**: `useInboundForecastVM`, `useUkeireForecastVM` (後方互換)
- **UI**: `ForecastCard`
- **Ports**: `IInboundForecastRepository`

## 依存方向

- `domain/` の型と services を使用
- `kpi-targets` と `inbound-monthly` の UI コンポーネント props を生成
