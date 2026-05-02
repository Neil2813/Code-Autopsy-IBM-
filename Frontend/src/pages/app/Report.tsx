import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { PageHeader } from "@/components/PageHeader";
import { reportService } from "@/lib/api/services";
import { toast } from "@/hooks/use-toast";
import type { ReportResponse } from "@/types/api";

const SECTIONS = [
  { id: "summary", label: "Summary" },
  { id: "architecture", label: "Architecture overview" },
  { id: "risks", label: "Risks" },
  { id: "suggestions", label: "Suggestions" },
  { id: "dependencies", label: "Dependency graph" },
  { id: "migration_blockers", label: "Migration blockers" },
  { id: "next_steps", label: "Next steps" },
  { id: "snippets", label: "Code snippets" },
];

const reportDownloadMeta: Record<string, { extension: string; type: string }> = {
  markdown: { extension: "md", type: "text/markdown" },
  json: { extension: "json", type: "application/json" },
  html: { extension: "html", type: "text/html" },
  pdf: { extension: "pdf", type: "application/pdf" },
};

const base64ToBlob = (value: string, type: string) => {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Blob([bytes], { type });
};

const Report = () => {
  const { jobId = "" } = useParams();
  const [format, setFormat] = useState("markdown");
  const [sections, setSections] = useState<string[]>(SECTIONS.map((s) => s.id));
  const [lastReport, setLastReport] = useState<ReportResponse | null>(null);

  const generate = useMutation({
    mutationFn: () => reportService.generate(jobId, format, sections),
    onSuccess: (res) => {
      setLastReport(res.data);
      toast({ title: "Report generated", description: `${res.data.format.toUpperCase()} report is ready.` });
    },
    onError: (e: any) => toast({ title: "Failed", description: e?.message ?? "Backend not reachable.", variant: "destructive" }),
  });

  const toggle = (id: string) =>
    setSections((prev) => prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]);

  return (
    <div className="mx-auto w-full max-w-5xl">
      <PageHeader title="Generate report" description="Create a downloadable summary of this analysis." />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Configuration</CardTitle></CardHeader>
          <CardContent className="space-y-6">
            <div>
              <Label className="text-sm font-medium">Format</Label>
              <RadioGroup value={format} onValueChange={setFormat} className="mt-2 grid grid-cols-2 gap-3 sm:grid-cols-4">
                {["markdown","json","html","pdf"].map((f) => (
                  <Label key={f} htmlFor={f} className="flex cursor-pointer items-center gap-2 rounded-md border border-border bg-card px-3 py-2 hover:border-primary/40">
                    <RadioGroupItem id={f} value={f} />
                    <span className="text-sm uppercase">{f}</span>
                  </Label>
                ))}
              </RadioGroup>
            </div>

            <div>
              <Label className="text-sm font-medium">Sections</Label>
              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                {SECTIONS.map((s) => (
                  <Label key={s.id} className="flex cursor-pointer items-center gap-2 rounded-md border border-border bg-card px-3 py-2 hover:border-primary/40">
                    <Checkbox checked={sections.includes(s.id)} onCheckedChange={() => toggle(s.id)} />
                    <span className="text-sm">{s.label}</span>
                  </Label>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Actions</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Button className="w-full" onClick={() => generate.mutate()} disabled={generate.isPending}>
              {generate.isPending ? "Generating..." : "Generate report"}
            </Button>
            {lastReport?.content && (
              <Button
                className="w-full"
                variant="outline"
                onClick={() => {
                  const meta = reportDownloadMeta[lastReport.format] || reportDownloadMeta.markdown;
                  const blob = lastReport.format === "pdf"
                    ? base64ToBlob(lastReport.content || "", meta.type)
                    : new Blob([lastReport.content || ""], { type: meta.type });
                  const url = URL.createObjectURL(blob);
                  const link = document.createElement("a");
                  link.href = url;
                  link.download = `modernization-report.${meta.extension}`;
                  link.click();
                  URL.revokeObjectURL(url);
                }}
              >
                Download generated
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
      {lastReport?.content && (
        <Card className="mt-6">
          <CardHeader><CardTitle>Preview</CardTitle></CardHeader>
          <CardContent>
            {lastReport.format === "html" ? (
              <iframe title="HTML report preview" className="h-[420px] w-full rounded-md border bg-white" srcDoc={lastReport.content} />
            ) : lastReport.format === "pdf" ? (
              <p className="rounded-md bg-muted p-4 text-sm text-muted-foreground">PDF report generated. Use Download generated to save it.</p>
            ) : (
              <pre className="max-h-[420px] overflow-auto rounded-md bg-muted p-4 text-xs">{lastReport.content}</pre>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Report;
