/**
 * SeverityBadge — colour-coded inline badge for alert severity levels.
 *
 * Purely presentational; renders a <span> with pre-defined Tailwind classes
 * that map severity level → background/text colour combination.
 *
 * Colour palette is shared with SeverityChart.tsx and ZoneMap.tsx so that
 * the same severity always appears in the same colour throughout the UI.
 * If the palette needs to change, update all three files together.
 *
 * The `badge` utility class is defined in index.css and provides base padding,
 * font size, and border-radius so individual severity styles only need to
 * specify colours.
 */
import type { Severity } from '../types';

const STYLES: Record<Severity, string> = {
  low:      'bg-green-100  text-green-800',
  medium:   'bg-yellow-100 text-yellow-800',
  high:     'bg-orange-100 text-orange-800',
  critical: 'bg-red-100    text-red-800',
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={`badge ${STYLES[severity]} capitalize`}>
      {severity}
    </span>
  );
}
