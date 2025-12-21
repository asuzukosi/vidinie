export function CircularProgress({
    completed,
    total,
  }: {
    completed: number;
    total: number;
  }) {
    const progress = total > 0 ? ((total - completed) / total) * 100 : 0;
    const strokeDashoffset = 100 - progress;
  
    return (
      <svg
        className="-rotate-90 scale-y-[-1]"
        height="14"
        width="14"
        viewBox="0 0 14 14"
      >
        <circle
          className="stroke-muted"
          cx="7"
          cy="7"
          fill="none"
          r="6"
          strokeWidth="2"
          pathLength="100"
        />
        <circle
          className="stroke-primary"
          cx="7"
          cy="7"
          fill="none"
          r="6"
          strokeWidth="2"
          pathLength="100"
          strokeDasharray="100"
          strokeLinecap="round"
          style={{ strokeDashoffset }}
        />
      </svg>
    );
  }