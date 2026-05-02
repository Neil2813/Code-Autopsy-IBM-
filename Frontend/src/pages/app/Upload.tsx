import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { analysisService, uploadService } from "@/lib/api/services";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

const Upload = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const [projectName, setProjectName] = useState("");
  const [description, setDescription] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [snippet, setSnippet] = useState("");
  const [language, setLanguage] = useState("java");

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (accepted) => setFiles((prev) => [...prev, ...accepted]),
  });

  const filesMutation = useMutation({
    mutationFn: async () => {
      const res = await uploadService.uploadFiles(files, projectName);
      await analysisService.start(res.data.job_id);
      return res;
    },
    onSuccess: (res) => navigate(`/analysis/${res.data.job_id}`),
    onError: (e: any) => toast({ title: "Upload failed", description: e?.message ?? "Backend not reachable.", variant: "destructive" }),
  });

  const repoMutation = useMutation({
    mutationFn: async () => {
      const res = await uploadService.uploadRepository(repoUrl, "main", projectName);
      await analysisService.start(res.data.job_id);
      return res;
    },
    onSuccess: (res) => navigate(`/analysis/${res.data.job_id}`),
    onError: (e: any) => toast({ title: "Upload failed", description: e?.message ?? "Backend not reachable.", variant: "destructive" }),
  });

  const snippetMutation = useMutation({
    mutationFn: async () => {
      const res = await uploadService.uploadSnippet(snippet, language, projectName, description);
      await analysisService.start(res.data.job_id);
      return res;
    },
    onSuccess: (res) => navigate(`/analysis/${res.data.job_id}`),
    onError: (e: any) => toast({ title: "Upload failed", description: e?.message ?? "Backend not reachable.", variant: "destructive" }),
  });

  const totalSize = files.reduce((s, f) => s + f.size, 0);

  return (
    <div className="mx-auto w-full max-w-4xl space-y-6 py-2 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-foreground font-heading leading-tight">
          New analysis
        </h1>
        <div className="flex items-baseline gap-2">
          <h2 className="text-xl font-semibold text-muted-foreground font-heading">
            Upload codebase.
          </h2>
          <p className="text-sm text-muted-foreground/50 font-sans">
            Generate your modernization plan.
          </p>
        </div>
      </div>

      <div className="space-y-5">
        <div className="grid gap-6 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="project" className="text-[10px] font-bold tracking-widest text-muted-foreground/60 uppercase font-sans">Project name</Label>
            <Input 
              id="project" 
              value={projectName} 
              onChange={(e) => setProjectName(e.target.value)} 
              placeholder="Order service v1" 
              className="h-10 bg-muted/20 border-border/50 focus-visible:ring-primary/50 transition-all text-sm font-sans"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-[10px] font-bold tracking-widest text-muted-foreground/60 uppercase font-sans">Language</Label>
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger className="h-10 bg-muted/20 border-border/50 focus:ring-primary/50 text-sm font-sans">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto-detect</SelectItem>
                <SelectItem value="java">Java</SelectItem>
                <SelectItem value="cobol">COBOL</SelectItem>
                <SelectItem value="rpg">RPG</SelectItem>
                <SelectItem value="jcl">JCL</SelectItem>
                <SelectItem value="mainframe">Mainframe</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="desc" className="text-[10px] font-bold tracking-widest text-muted-foreground/60 uppercase font-sans">Description</Label>
          <Textarea 
            id="desc" 
            value={description} 
            onChange={(e) => setDescription(e.target.value)} 
            placeholder="Optional context..." 
            className="min-h-[80px] bg-muted/20 border-border/50 focus-visible:ring-primary/50 text-sm resize-none font-sans"
          />
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-xl font-bold tracking-tight font-heading">Source</h3>
        
        <Tabs defaultValue="files" className="w-full">
          <TabsList className="grid w-full grid-cols-3 h-12 bg-muted/30 p-1 rounded-xl border border-border/40">
            <TabsTrigger value="files" className="rounded-lg data-[state=active]:bg-card data-[state=active]:text-primary data-[state=active]:shadow-sm transition-all font-medium text-sm font-sans">
              Files
            </TabsTrigger>
            <TabsTrigger value="repo" className="rounded-lg data-[state=active]:bg-card data-[state=active]:text-primary data-[state=active]:shadow-sm transition-all font-medium text-sm font-sans">
              Repository
            </TabsTrigger>
            <TabsTrigger value="snippet" className="rounded-lg data-[state=active]:bg-card data-[state=active]:text-primary data-[state=active]:shadow-sm transition-all font-medium text-sm font-sans">
              Snippet
            </TabsTrigger>
          </TabsList>

          <TabsContent value="files" className="mt-6 space-y-4">
            <div
              {...getRootProps()}
              className={`group flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed py-8 px-6 text-center transition-all duration-300 ${
                isDragActive 
                ? "border-primary bg-primary/5" 
                : "border-border/60 hover:border-primary/40 hover:bg-muted/10"
              }`}
            >
              <input {...getInputProps()} />
              <div className={cn(
                "mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted/40 transition-transform group-hover:scale-110 duration-300",
                isDragActive && "bg-primary/10"
              )}>
              </div>
              <p className="text-base font-semibold tracking-tight font-sans">
                {isDragActive ? "Drop files here" : "Drag & drop files or ZIP archives"}
              </p>
              <p className="mt-1 text-xs text-muted-foreground/60 font-sans">
                Or click to browse from computer
              </p>
            </div>

            {files.length > 0 && (
              <div className="space-y-4 animate-in slide-in-from-top-2 duration-400">
                <div className="grid gap-2 max-h-[160px] overflow-y-auto pr-2 custom-scrollbar">
                  {files.map((f, i) => (
                    <div key={i} className="flex items-center justify-between rounded-lg border border-border/50 bg-card/50 p-3 backdrop-blur-sm group hover:border-primary/30 transition-colors">
                      <div className="flex items-center gap-3 truncate">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted/50">
                        </div>
                        <div className="flex flex-col truncate">
                          <span className="truncate font-medium text-xs font-sans">{f.name}</span>
                          <span className="text-[10px] text-muted-foreground font-sans">{(f.size / 1024).toFixed(1)} KB</span>
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" className="h-7 w-7 rounded-full hover:bg-destructive/10 hover:text-destructive" onClick={() => setFiles((prev) => prev.filter((_, j) => j !== i))}>
                        <X className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  ))}
                </div>
                <div className="flex items-center justify-between border-t border-border/50 pt-4">
                  <div className="flex flex-col">
                    <span className="text-xs font-medium font-sans">Total size</span>
                    <span className="text-[10px] text-muted-foreground font-sans">{(totalSize / 1024).toFixed(1)} KB</span>
                  </div>
                  <Button 
                    size="sm" 
                    className="h-10 px-6 font-semibold shadow-lg shadow-primary/20 bg-primary hover:bg-primary/90 text-primary-foreground font-sans"
                    onClick={() => filesMutation.mutate()} 
                    disabled={filesMutation.isPending}
                  >
                    {filesMutation.isPending ? "Uploading..." : "Start analysis"}
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="repo" className="mt-6 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="repo" className="text-[10px] font-bold tracking-widest text-muted-foreground/60 uppercase font-sans">Git repository URL</Label>
              <Input 
                id="repo" 
                value={repoUrl} 
                onChange={(e) => setRepoUrl(e.target.value)} 
                placeholder="https://github.com/org/repo.git" 
                className="h-12 bg-muted/20 border-border/50 focus-visible:ring-primary/50 text-sm font-sans"
              />
            </div>
            <Button 
              size="lg"
              className="w-full h-12 font-semibold shadow-lg shadow-primary/20 bg-primary hover:bg-primary/90 text-primary-foreground font-sans"
              onClick={() => repoMutation.mutate()} 
              disabled={!repoUrl || repoMutation.isPending}
            >
              {repoMutation.isPending ? "Cloning..." : "Start analysis"}
            </Button>
          </TabsContent>

          <TabsContent value="snippet" className="mt-6 space-y-4">
            <Textarea
              value={snippet}
              onChange={(e) => setSnippet(e.target.value)}
              placeholder="Paste code..."
              className="font-mono text-sm min-h-[200px] max-h-[300px] bg-muted/20 border-border/50 focus-visible:ring-primary/50 p-4 rounded-xl"
            />
            <Button 
              size="lg"
              className="w-full h-12 font-semibold shadow-lg shadow-primary/20 bg-primary hover:bg-primary/90 text-primary-foreground font-sans"
              onClick={() => snippetMutation.mutate()} 
              disabled={!snippet || snippetMutation.isPending}
            >
              {snippetMutation.isPending ? "Analyzing..." : "Start analysis"}
            </Button>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Upload;
