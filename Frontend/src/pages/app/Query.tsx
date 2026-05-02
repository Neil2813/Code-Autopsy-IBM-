import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { queryService } from "@/lib/api/services";

const SUGGESTED = [
  "What does this codebase do?",
  "Where are the main entry points?",
  "Which modules have circular dependencies?",
  "What's the highest risk file?",
];

const stripMarkdown = (value: string) =>
  value
    .replace(/```[\s\S]*?```/g, (block) => block.replace(/```[a-zA-Z]*\n?/g, "").replace(/```/g, ""))
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*[-*]\s+/gm, "- ")
    .trim();

const Query = () => {
  const { jobId = "" } = useParams();
  const [question, setQuestion] = useState("");
  const qc = useQueryClient();

  const history = useQuery({
    queryKey: ["query-history", jobId],
    queryFn: async () => (await queryService.history(jobId)).data,
    retry: false,
    enabled: !!jobId,
  });

  const ask = useMutation({
    mutationFn: (q: string) => queryService.ask(jobId, q),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["query-history", jobId] }); setQuestion(""); },
  });

  const messages = history.data?.messages ?? [];

  return (
    <div className="mx-auto flex h-[calc(100vh-9rem)] w-full max-w-4xl flex-col">
      <PageHeader title="Ask the codebase" description="Conversational Q&A grounded in your analysis." />

      <Card className="flex flex-1 flex-col overflow-hidden">
        <CardContent className="flex-1 space-y-4 overflow-y-auto p-6">
          {messages.length === 0 ? (
            <EmptyState
              imageSrc="/chatbot.png"
              title="Start a conversation"
              description="Ask anything about your codebase — architecture, risks, or modernization paths."
            />
          ) : (
            messages.map((m: any) => (
              <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
                  m.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary whitespace-pre-wrap leading-relaxed"
                }`}>
                  {m.role === "assistant" ? stripMarkdown(m.content) : m.content}
                </div>
              </div>
            ))
          )}
        </CardContent>

        <div className="border-t border-border p-4">
          {messages.length === 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {SUGGESTED.map((s) => (
                <button key={s} onClick={() => setQuestion(s)} className="rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground hover:border-primary/40 hover:text-foreground">
                  {s}
                </button>
              ))}
            </div>
          )}
          <form
            onSubmit={(e) => { e.preventDefault(); if (question.trim()) ask.mutate(question.trim()); }}
            className="flex gap-2"
          >
            <Input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a question..." />
            <Button type="submit" disabled={!question.trim() || ask.isPending}>
              {ask.isPending ? "..." : "Send"}
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
};

export default Query;
