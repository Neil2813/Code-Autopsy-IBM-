import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { History as HistoryIcon, Search } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { analysisService } from "@/lib/api/services";
import { format } from "date-fns";

const History = () => {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<string>("all");
  const jobs = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => (await analysisService.listJobs()).data,
    retry: false,
  });

  const list = (jobs.data?.jobs ?? []).filter((j: any) => {
    if (status !== "all" && j.status !== status) return false;
    if (search && !j.project_name?.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="mx-auto w-full max-w-7xl">
      <PageHeader title="Analysis history" description="All your past analyses in one place." actions={<Button asChild><Link to="/upload">New analysis</Link></Button>} />

      <div className="mb-4 flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Input placeholder="Search by project name..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="sm:w-48"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="processing">Processing</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          {jobs.isLoading ? (
            <div className="space-y-2 p-4">{[0,1,2,3].map((i) => <div key={i} className="h-14 animate-pulse rounded-md bg-secondary" />)}</div>
          ) : list.length ? (
            <table className="w-full text-sm">
              <thead className="border-b border-border bg-muted/40 text-left text-xs uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Project</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Languages</th>
                  <th className="px-4 py-3">Risk</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {list.map((j: any) => (
                  <tr key={j.id} className="border-b border-border last:border-0">
                    <td className="px-4 py-3 font-medium">{j.project_name}</td>
                    <td className="px-4 py-3"><Badge variant="outline">{j.status}</Badge></td>
                    <td className="px-4 py-3 text-muted-foreground">{j.languages?.join(", ") || "—"}</td>
                    <td className="px-4 py-3">{j.risk_score ?? "—"}</td>
                    <td className="px-4 py-3 text-muted-foreground">{j.created_at ? format(new Date(j.created_at), "PP") : "—"}</td>
                    <td className="px-4 py-3 text-right"><Button asChild variant="ghost" size="sm"><Link to={`/analysis/${j.id}`}>View</Link></Button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState
              title="No history yet"
              description="Once you run an analysis, it will show up here."
              action={<Button asChild><Link to="/upload">Start an analysis</Link></Button>}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default History;