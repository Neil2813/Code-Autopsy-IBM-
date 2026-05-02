import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

interface Props {
  icon?: LucideIcon;
  imageSrc?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}

export const EmptyState = ({ icon: Icon, imageSrc, title, description, action }: Props) => (
  <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/50 p-12 text-center">
    {(Icon || imageSrc) && (
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-accent/30 text-accent-foreground overflow-hidden">
        {imageSrc ? (
          <img src={imageSrc} alt="" className="h-10 w-10 object-contain" />
        ) : Icon ? (
          <Icon className="h-6 w-6" />
        ) : null}
      </div>
    )}
    <h3 className="text-base font-semibold">{title}</h3>
    {description && <p className="mt-1 max-w-sm text-sm text-muted-foreground">{description}</p>}
    {action && <div className="mt-6">{action}</div>}
  </div>
);