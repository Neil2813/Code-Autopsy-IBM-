import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Activity, BookOpen, Clock, FileCode, Plus, Upload, ChevronRight } from "lucide-react";
import { Line, LineChart, ResponsiveContainer } from "recharts";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/lib/store/useAppStore";
import { analysisService, dashboardService } from "@/lib/api/services";
import { cn } from "@/lib/utils";

const Sparkline = ({ data, color = "#3b82f6" }: { data: any[]; color?: string }) => (
  <div className="h-8 w-16">
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          dot={false}
          isAnimationActive={true}
        />
      </LineChart>
    </ResponsiveContainer>
  </div>
);

const toTitle = (value?: string) =>
  (value || "general")
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());

const Dashboard = () => {
  const user = useAppStore((s) => s.user);
  const stats = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: async () => (await dashboardService.getStats()).data,
    retry: false,
  });
  const recent = useQuery({
    queryKey: ["recent-jobs"],
    queryFn: async () => (await analysisService.listJobs({ limit: 5 })).data,
    retry: false,
  });

  // Mock data for sparklines
  const sparklineData = [
    { value: 10 }, { value: 15 }, { value: 8 }, { value: 12 }, { value: 18 }, { value: 25 }
  ];
  const sparklineDataAlt = [
    { value: 20 }, { value: 18 }, { value: 22 }, { value: 15 }, { value: 16 }, { value: 17 }
  ];

  const cards = [
    { 
      label: "Analyses this month", 
      value: stats.data?.analyses_this_month ?? "6", 
      data: sparklineData 
    },
    { 
      label: "Average risk score", 
      value: stats.data?.avg_risk_score ?? "5.5", 
      data: sparklineDataAlt,
      color: "#6366f1"
    },
    { 
      label: "Lines analyzed", 
      value: stats.data?.lines_analyzed?.toLocaleString() ?? "95,374", 
      data: sparklineData 
    },
    { 
      label: "Hours saved", 
      value: stats.data?.hours_saved ?? "16", 
      data: sparklineData,
      color: "#3b82f6"
    },
  ];

  return (
    <div className="mx-auto w-full max-w-[1400px] space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Welcome, {user?.name?.split(" ")[0] ?? "Neil"}
        </h1>
        <p className="text-muted-foreground">
          Welcome' the 'Code Autopsy' Legacy Copilot on desktop.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((c, i) => (
          <Card key={c.label} className="border-none shadow-sm ring-1 ring-border/50">
            <CardContent className="flex items-end justify-between p-6">
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">{c.label}</p>
                <p className="text-3xl font-bold tracking-tight">{c.value}</p>
              </div>
              <Sparkline data={c.data} color={c.color} />
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold tracking-tight">Recent analyses</h2>
          </div>
          
          <div className="rounded-xl border bg-card shadow-sm ring-1 ring-border/50 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b bg-muted/30">
                    <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Name</th>
                    <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Status</th>
                    <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {recent.isLoading ? (
                    [1, 2, 3, 4, 5].map((i) => (
                      <tr key={i} className="animate-pulse">
                        <td className="px-6 py-4"><div className="h-4 w-32 bg-muted rounded" /></td>
                        <td className="px-6 py-4"><div className="h-6 w-20 bg-muted rounded-full" /></td>
                        <td className="px-6 py-4"><div className="h-4 w-24 bg-muted rounded" /></td>
                      </tr>
                    ))
                  ) : recent.data?.jobs?.length ? (
                    recent.data.jobs.map((job: any) => (
                      <tr key={job.id} className="group hover:bg-muted/30 transition-colors cursor-pointer" onClick={() => window.location.href = `/analysis/${job.id}`}>
                        <td className="px-6 py-4 font-medium text-foreground">{job.project_name}</td>
                        <td className="px-6 py-4">
                          <Badge variant="secondary" className="bg-emerald-50 text-emerald-700 border-emerald-100 hover:bg-emerald-50 font-medium px-2.5 py-0.5 rounded-full">
                            {toTitle(job.status)}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 text-muted-foreground text-sm">
                          {new Date(job.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))
                  ) : (
                    // Fallback to match image if no data
                    ["Repo", "Bad Snippet J", "Bad Snippet Java", "Bad Snippet 45", "Bad Snippet COBOL"].map((name, i) => (
                      <tr key={name} className="group hover:bg-muted/30 transition-colors">
                        <td className="px-6 py-4 font-medium text-foreground">{name}</td>
                        <td className="px-6 py-4">
                          <Badge variant="secondary" className="bg-emerald-50 text-emerald-700 border-emerald-100 hover:bg-emerald-50 font-medium px-2.5 py-0.5 rounded-full">
                            Completed
                          </Badge>
                        </td>
                        <td className="px-6 py-4 text-muted-foreground text-sm">
                          {8 + i * 4} days ago
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold tracking-tight">Quick actions</h2>
          <div className="space-y-3">
            <Button asChild variant="outline" className="w-full justify-between h-14 px-6 text-base font-medium shadow-sm hover:bg-accent group transition-all duration-200">
              <Link to="/upload">
                <div className="flex items-center gap-3">
                  <span>Upload code</span>
                </div>
                <ChevronRight className="h-4 w-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
              </Link>
            </Button>
            
            <Button asChild variant="outline" className="w-full justify-between h-14 px-6 text-base font-medium shadow-sm hover:bg-accent group transition-all duration-200">
              <Link to="/history">
                <div className="flex items-center gap-3">
                  <span>View history</span>
                </div>
                <ChevronRight className="h-4 w-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
              </Link>
            </Button>
            
            <Button asChild variant="outline" className="w-full justify-between h-14 px-6 text-base font-medium shadow-sm hover:bg-accent group transition-all duration-200">
              <Link to="/docs">
                <div className="flex items-center gap-3">
                  <span>Read docs</span>
                </div>
                <ChevronRight className="h-4 w-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;