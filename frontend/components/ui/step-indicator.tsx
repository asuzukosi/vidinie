import { IconCircleCheckFilled, IconCircleDashed } from "@tabler/icons-react";

export function StepIndicator({ completed }: { completed: boolean }) {
    if (completed) {
      return (
        <IconCircleCheckFilled
          className="mt-1 size-4.5 shrink-0 text-primary"
          aria-hidden="true"
        />
      );
    }
    return (
      <IconCircleDashed
        className="mt-1 size-5 shrink-0 stroke-muted-foreground/40"
        strokeWidth={2}
        aria-hidden="true"
      />
    );
}
