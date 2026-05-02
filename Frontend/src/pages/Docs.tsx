import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";

const sections = [
  { title: "Getting started", body: "Create an account, upload your codebase, and run your first analysis in under five minutes." },
  { title: "Upload methods", body: "You can upload ZIP archives, individual files, connect a Git repository, or paste a code snippet." },
  { title: "Understanding results", body: "Reports include a risk score, maintainability index, dependency graph, and prioritized suggestions." },
  { title: "Query interface", body: "Ask natural-language questions about your codebase and receive grounded, source-referenced answers." },
  { title: "Reports", body: "Export your analysis as Markdown, HTML, JSON or PDF for sharing with stakeholders." },
  { title: "FAQ", body: "Common questions and troubleshooting tips for working with legacy code analyses." },
];

const Docs = () => (
  <div className="min-h-screen bg-[#000000] text-white">
    <div className="container max-w-4xl py-24">
      <PageHeader 
        title="Documentation" 
        description="Learn how to get the most out of Code Autopsy." 
      />
      <div className="space-y-6 mt-12">
        {sections.map((s) => (
          <Card key={s.title} className="bg-zinc-900/50 border-white/10 text-white backdrop-blur-sm">
            <CardHeader><CardTitle className="text-xl font-bold">{s.title}</CardTitle></CardHeader>
            <CardContent>
              <p className="text-sm text-zinc-400 leading-relaxed">{s.body}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  </div>
);

export default Docs;