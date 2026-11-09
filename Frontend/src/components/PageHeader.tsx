import { ReactNode } from "react";

interface Props {
  title: string;
  description?: string;
  actions?: ReactNode;
  badge?: string;
}

export const PageHeader = ({ title, description, actions, badge }: Props) => (
  <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between pb-6 border-b border-border/40">
    <div className="space-y-1">
      {badge && (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-primary/10 text-primary border border-primary/20 mb-1">
          {badge}
        </span>
      )}
      <h1 className="text-2xl font-bold tracking-tight md:text-3xl font-heading text-foreground">
        {title}
      </h1>
      {description && (
        <p className="text-sm text-muted-foreground font-sans max-w-2xl">
          {description}
        </p>
      )}
    </div>
    {actions && <div className="flex items-center gap-2.5 shrink-0">{actions}</div>}
  </div>
);
