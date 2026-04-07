# Components — Reusable UI Components

Shared React components composed by page components. Each component handles one focused piece of UI.

## Files

| File | Description |
|------|-------------|
| `AlertPanel.tsx` | Sidebar panel showing recent unacknowledged alerts in real time |
| `AlertsBrowserModal.tsx` | Modal for browsing and filtering full alert history |
| `AggregationHistoryChart.tsx` | Recharts line/bar chart for 5-minute or hourly rollup data |
| `ConfirmDialog.tsx` | Generic confirmation dialog used for destructive actions |
| `MetricGauge.tsx` | Circular gauge displaying a current sensor reading vs. threshold |
| `PipelineHealthIndicator.tsx` | Status indicator showing whether MQTT ingestion is active |
| `PublicLandingMap.tsx` | Leaflet map rendered on the public landing page with zone markers |
| `PublicZoneStatusCards.tsx` | Summary cards showing zone health for the public view |
| `ScemasLogoMark.tsx` | SVG logo mark used in the nav bar |
| `SeverityBadge.tsx` | Coloured pill badge for alert severity levels (low / medium / high / critical) |
| `SeverityChart.tsx` | Pie or bar chart breaking down alerts by severity |
| `ThresholdFormModal.tsx` | Modal form for creating and editing thresholds |
| `ThresholdTable.tsx` | Sortable table listing all thresholds with edit/delete actions |
| `ViolationAlertModal.tsx` | Modal that pops when a new critical violation alert arrives via SSE |
| `ZoneMap.tsx` | Authenticated dashboard map showing live zone status |
