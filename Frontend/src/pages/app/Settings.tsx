import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/PageHeader";
import { useAppStore } from "@/lib/store/useAppStore";
import { getApiBaseUrl, setApiBaseUrl } from "@/lib/api/client";
import { toast } from "@/hooks/use-toast";

const Settings = () => {
  const { theme, toggleTheme } = useAppStore();
  const [apiUrl, setApiUrl] = useState(getApiBaseUrl());

  return (
    <div className="mx-auto w-full max-w-3xl space-y-8 py-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight text-foreground font-heading">Settings</h1>
        <p className="text-muted-foreground font-sans">Configure your workspace preferences and identity.</p>
      </div>

      <Card className="border-none shadow-sm ring-1 ring-border/50 bg-card/50 backdrop-blur-sm overflow-hidden">
        <CardHeader className="pb-4">
          <CardTitle className="text-xl font-bold font-heading text-primary">Appearance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between group">
            <div className="space-y-0.5">
              <Label htmlFor="dark" className="text-base font-semibold font-sans cursor-pointer">Dark mode</Label>
              <p className="text-xs text-muted-foreground font-sans">Switch between light and dark themes.</p>
            </div>
            <Switch id="dark" checked={theme === "dark"} onCheckedChange={toggleTheme} className="data-[state=checked]:bg-primary" />
          </div>
        </CardContent>
      </Card>

      <Card className="border-none shadow-sm ring-1 ring-border/50 bg-card/50 backdrop-blur-sm overflow-hidden">
        <CardHeader className="pb-4">
          <CardTitle className="text-xl font-bold font-heading text-primary">Localization</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-6 sm:grid-cols-2">
          <div className="space-y-2">
            <Label className="text-xs font-bold tracking-widest text-muted-foreground/60 uppercase font-sans">Language</Label>
            <Select defaultValue="en">
              <SelectTrigger className="h-10 bg-muted/20 border-border/50 focus:ring-primary/50 text-sm font-sans">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English (US)</SelectItem>
                <SelectItem value="es">Español</SelectItem>
                <SelectItem value="fr">Français</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label className="text-xs font-bold tracking-widest text-muted-foreground/60 uppercase font-sans">Timezone</Label>
            <Select defaultValue="utc">
              <SelectTrigger className="h-10 bg-muted/20 border-border/50 focus:ring-primary/50 text-sm font-sans">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="utc">UTC (Coordinated Universal Time)</SelectItem>
                <SelectItem value="est">EST (Eastern Standard Time)</SelectItem>
                <SelectItem value="pst">PST (Pacific Standard Time)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;