import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Activity, BookOpen, Clock, FileCode, Plus, Upload, ChevronRight } from "lucide-react";
import { Line, LineChart, ResponsiveContainer } from "recharts";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/lib/store/useAppStore";
import { analysisService, dashboardService, bobService } from "@/lib/api/services";
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

  // Fetch migration score for the most recent completed job
  const latestJobId = recent.data?.jobs?.find((j: any) => j.status === "completed")?.id;
  const migrationScore = useQuery({
    queryKey: ["migration-score", latestJobId],
    queryFn: async () => (await bobService.migrationScore(latestJobId!)).data,
    enabled: !!latestJobId,
    retry: false,
  });

  // When database has 0 jobs, purge any stale browser localStorage from old DB sessions
  useEffect(() => {
    if (stats.data && stats.data.analyses_this_month === 0 && (!recent.data?.jobs?.length)) {
      analysisService.clearJobs?.();
    }
  }, [stats.data, recent.data]);

  const hasActivity = Boolean(
    (stats.data?.analyses_this_month && stats.data.analyses_this_month > 0) ||
    (stats.data?.lines_analyzed && stats.data.lines_analyzed > 0)
  );

  const sparklineData = hasActivity
    ? [ { value: 10 }, { value: 15 }, { value: 8 }, { value: 12 }, { value: 18 }, { value: 25 } ]
    : [ { value: 0 }, { value: 0 }, { value: 0 }, { value: 0 }, { value: 0 }, { value: 0 } ];
  const sparklineDataAlt = hasActivity
    ? [ { value: 20 }, { value: 18 }, { value: 22 }, { value: 15 }, { value: 16 }, { value: 17 } ]
    : [ { value: 0 }, { value: 0 }, { value: 0 }, { value: 0 }, { value: 0 }, { value: 0 } ];

  const cards = [
    { 
      label: "Analyses this month", 
      value: stats.data?.analyses_this_month ?? 0, 
      data: sparklineData 
    },
    { 
      label: "Average risk score", 
      value: (stats.data?.avg_risk_score !== null && stats.data?.avg_risk_score !== undefined) 
        ? stats.data.avg_risk_score 
        : 0, 
      data: sparklineDataAlt,
      color: "#6366f1"
    },
    { 
      label: "Lines analyzed", 
      value: (stats.data?.lines_analyzed !== null && stats.data?.lines_analyzed !== undefined) 
        ? stats.data.lines_analyzed.toLocaleString() 
        : "0", 
      data: sparklineData 
    },
    { 
      label: "Hours saved", 
      value: stats.data?.hours_saved ?? 0, 
      data: sparklineData,
      color: "#3b82f6"
    },
  ];

  return (
    <div className="mx-auto w-full max-w-[1400px] space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="border-primary/20 bg-primary/5 text-primary text-xs font-semibold px-2.5 py-0.5 rounded-full">
            Enterprise Copilot
          </Badge>
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground font-heading">
          Welcome back, {user?.name?.split(" ")[0] ?? "Neil"}
        </h1>
        <p className="text-sm text-muted-foreground font-sans">
          Enterprise legacy modernization, automated risk diagnostics, and architectural refactoring.
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

      {/* Migration Readiness Score */}
      {migrationScore.data && (
        <Card className="border-none shadow-sm ring-1 ring-border/50">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h2 className="text-xl font-semibold tracking-tight">Migration Readiness</h2>
                <p className="text-sm text-muted-foreground">{migrationScore.data.summary}</p>
              </div>
              <div className="flex flex-col items-center">
                <div className="relative h-20 w-20 flex items-center justify-center">
                  <svg className="absolute h-20 w-20 -rotate-90" viewBox="0 0 36 36">
                    <circle cx="18" cy="18" r="15" fill="none" stroke="currentColor" strokeWidth="3" className="text-muted/20" />
                    <circle cx="18" cy="18" r="15" fill="none" stroke="url(#scoreGrad)" strokeWidth="3" strokeDasharray={`${migrationScore.data.overall_score * 0.94} 94`} strokeLinecap="round" />
                    <defs><linearGradient id="scoreGrad"><stop offset="0%" stopColor="#3b82f6" /><stop offset="100%" stopColor="#6366f1" /></linearGradient></defs>
                  </svg>
                  <span className="text-2xl font-bold">{migrationScore.data.overall_score}</span>
                </div>
                <Badge variant="secondary" className="mt-1 font-mono">Grade {migrationScore.data.grade}</Badge>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-5 gap-2">
              {Object.entries(migrationScore.data.sub_scores).map(([key, val]) => (
                <div key={key} className="text-center">
                  <div className="text-xs text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</div>
                  <div className="text-sm font-semibold">{String(val)}</div>
                </div>
              ))}
            </div>
            {migrationScore.data.top_blockers.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {migrationScore.data.top_blockers.map((b: string, i: number) => (
                  <Badge key={i} variant="outline" className="text-xs font-normal">{b}</Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

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
                    <tr>
                      <td colSpan={3} className="px-6 py-12 text-center">
                        <div className="flex flex-col items-center justify-center space-y-2">
                          <p className="text-sm font-semibold text-foreground">No analyses yet</p>
                          <p className="text-xs text-muted-foreground max-w-sm">
                            Your audit and modernization history will appear here once you run your first analysis.
                          </p>
                          <Button asChild size="sm" className="mt-2 text-xs rounded-lg">
                            <Link to="/upload">Start New Analysis</Link>
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold tracking-tight">Quick actions</h2>
          <div className="space-y-3">
            <Button asChild variant="outline" className="w-full justify-between h-14 px-5 text-sm font-medium shadow-sm border-border/60 hover:bg-muted/60 group transition-all duration-200 rounded-xl">
              <Link to="/upload">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Upload className="h-4 w-4" />
                  </div>
                  <span className="font-semibold text-foreground">Upload codebase</span>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
              </Link>
            </Button>
            
            <Button asChild variant="outline" className="w-full justify-between h-14 px-5 text-sm font-medium shadow-sm border-border/60 hover:bg-muted/60 group transition-all duration-200 rounded-xl">
              <Link to="/history">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-500">
                    <Clock className="h-4 w-4" />
                  </div>
                  <span className="font-semibold text-foreground">Audit history</span>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
              </Link>
            </Button>
            
            <Button asChild variant="outline" className="w-full justify-between h-14 px-5 text-sm font-medium shadow-sm border-border/60 hover:bg-muted/60 group transition-all duration-200 rounded-xl">
              <Link to="/docs">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
                    <BookOpen className="h-4 w-4" />
                  </div>
                  <span className="font-semibold text-foreground">Documentation</span>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;