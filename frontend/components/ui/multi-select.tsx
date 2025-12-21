"use client";

import * as React from "react";
import { ChevronDownIcon, XIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Checkbox } from "@/components/ui/checkbox";

interface MultiSelectOption {
  value: string;
  label: string;
}

interface MultiSelectProps {
  options: MultiSelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  className?: string;
  id?: string;
}

export function MultiSelect({
  options,
  value,
  onChange,
  placeholder = "Select items...",
  className,
  id,
}: MultiSelectProps) {
  const [open, setOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [open]);

  const handleSelect = (optionValue: string) => {
    const newValue = value.includes(optionValue)
      ? value.filter((v) => v !== optionValue)
      : [...value, optionValue];
    onChange(newValue);
  };

  const handleRemove = (optionValue: string, e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(value.filter((v) => v !== optionValue));
  };

  const selectedLabels = options
    .filter((opt) => value.includes(opt.value))
    .map((opt) => opt.label);

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <button
        id={id}
        type="button"
        onClick={() => setOpen(!open)}
        className={cn(
          "border-input focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 dark:hover:bg-input/50 flex w-full items-center justify-between gap-2 rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 h-9",
          value.length === 0 && "text-muted-foreground"
        )}
      >
        <div className="flex flex-1 flex-wrap gap-1 overflow-hidden text-left">
          {value.length === 0 ? (
            <span className="text-muted-foreground">{placeholder}</span>
          ) : (
            <div className="flex flex-wrap gap-1">
              {selectedLabels.slice(0, 2).map((label, idx) => {
                const option = options.find((opt) => opt.label === label);
                return (
                  <span
                    key={option?.value || idx}
                    className="inline-flex items-center gap-1 rounded bg-zinc-100 px-2 py-0.5 text-xs dark:bg-zinc-800"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemove(option!.value, e);
                    }}
                  >
                    {label}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemove(option!.value, e);
                      }}
                      className="ml-1 rounded-full hover:bg-zinc-200 dark:hover:bg-zinc-700"
                    >
                      <XIcon className="h-3 w-3" />
                    </button>
                  </span>
                );
              })}
              {value.length > 2 && (
                <span className="text-xs text-muted-foreground">
                  +{value.length - 2} more
                </span>
              )}
            </div>
          )}
        </div>
        <ChevronDownIcon
          className={cn(
            "size-4 opacity-50 transition-transform",
            open && "rotate-180"
          )}
        />
      </button>
      {open && (
        <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95">
          <div className="max-h-96 overflow-y-auto p-1">
            {options.map((option) => {
              const isSelected = value.includes(option.value);
              return (
                <div
                  key={option.value}
                  className="relative flex w-full cursor-pointer items-center gap-2 rounded-sm py-1.5 pl-2 pr-8 text-sm outline-none select-none hover:bg-accent hover:text-accent-foreground"
                  onClick={() => handleSelect(option.value)}
                >
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => handleSelect(option.value)}
                  />
                  <span>{option.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

