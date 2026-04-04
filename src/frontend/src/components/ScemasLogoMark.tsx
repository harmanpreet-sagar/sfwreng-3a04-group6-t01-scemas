type Props = {
  className?: string;
};

/**
 * SCEMAS mark: three rising readings + baseline (air / noise / climate signals).
 */
export function ScemasLogoMark({ className }: Props) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M5 18V11" />
      <path d="M12 18V5" />
      <path d="M19 18V8" />
      <path d="M3 18.25h18" />
    </svg>
  );
}
