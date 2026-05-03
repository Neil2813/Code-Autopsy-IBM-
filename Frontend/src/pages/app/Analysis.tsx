import { Fragment } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  FileText,
  FolderTree,
  GitBranch,
  Loader2,
  MessageSquare,
  Network,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { analysisService } from "@/lib/api/services";

const STAGES = ["Upload", "Parsing", "Analysis", "Risk detection", "Suggestions"];

const severityColor: Record<string, string> = {
  critical: "bg-destructive text-destructive-foreground",
  high: "bg-destructive/80 text-destructive-foreground",
  medium: "bg-warning text-warning-foreground",
  low: "bg-success text-success-foreground",
  info: "bg-secondary text-secondary-foreground",
};

const priorityRank: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

const fileRiskLabel = (severity?: string) => {
  const value = (severity || "unknown").toLowerCase();
  return value === "unknown" ? "File risk: -" : `File risk: ${value.toUpperCase()}`;
};

const effortBySeverity: Record<string, string> = {
  critical: "high",
  high: "medium",
  medium: "medium",
  low: "low",
  info: "low",
};

type TreeNode = {
  name: string;
  path: string;
  children: TreeNode[];
  isFile?: boolean;
};

type DependencyGraphNode = {
  id: string;
  name?: string;
  label?: string;
  type?: string;
  file_path?: string;
};

type DependencyGraphEdge = {
  from: string;
  to: string;
  label?: string;
  weight?: number;
};

type DependencyOverview = {
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
  summary: string;
  mode: string;
  totalNodes: number;
  totalEdges: number;
};

const toTitle = (value?: string) =>
  (value || "general")
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());

const basename = (value?: string) => String(value || "").split(/[\\/]/).filter(Boolean).pop() || String(value || "");

const nodeLabel = (node?: DependencyGraphNode) => basename(node?.label || node?.name || node?.file_path || node?.id || "Node");

const edgeLabel = (edge: DependencyGraphEdge) => toTitle(edge.label || "depends on");

const normalizeGraphPath = (value?: string) => String(value || "").replace(/\\/g, "/").replace(/^[A-Za-z]:\//, "");

const buildStructuralDependencyMap = (graphNodes: DependencyGraphNode[]): Pick<DependencyOverview, "nodes" | "edges"> => {
  const nodes = new Map<string, DependencyGraphNode>();
  const edges = new Map<string, DependencyGraphEdge>();
  const paths = graphNodes
    .map((node) => ({
      original: node,
      path: normalizeGraphPath(node.file_path || node.id),
    }))
    .filter((item) => item.path)
    .sort((a, b) => a.path.localeCompare(b.path))
    .slice(0, 56);

  nodes.set("root", { id: "root", label: "Codebase", type: "root" });

  paths.forEach(({ original, path }) => {
    const parts = path.split("/").filter(Boolean);
    let parentId = "root";
    let currentPath = "";

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part;
      const isFile = index === parts.length - 1;
      const nodeId = isFile ? original.id : `folder:${currentPath}`;

      if (!nodes.has(nodeId)) {
        nodes.set(nodeId, {
          ...original,
          id: nodeId,
          label: part,
          name: part,
          file_path: isFile ? original.file_path || path : currentPath,
          type: isFile ? original.type || "file" : "folder",
        });
      }

      const edgeId = `${parentId}->${nodeId}`;
      if (!edges.has(edgeId)) {
        edges.set(edgeId, {
          from: parentId,
          to: nodeId,
          label: isFile ? "contains" : "module",
        });
      }

      parentId = nodeId;
    });
  });

  return {
    nodes: Array.from(nodes.values()),
    edges: Array.from(edges.values()),
  };
};

const getRiskFileRef = (risk: any, filePath?: string) => {
  const refs = Array.isArray(risk?.affected_files) ? risk.affected_files : [];
  const match = refs.find((ref: any) => {
    const refPath = typeof ref === "string" ? ref : ref?.file_path;
    return filePath ? refPath === filePath : Boolean(refPath);
  });
  return typeof match === "string" ? { file_path: match } : match || {};
};

const getRiskLine = (risk: any, filePath?: string) => {
  const ref = getRiskFileRef(risk, filePath);
  return ref?.line_start || ref?.line || risk?.line_start || risk?.line || null;
};

const getRiskSnippet = (risk: any, filePath?: string) => {
  const ref = getRiskFileRef(risk, filePath);
  return ref?.snippet || ref?.code_snippet || risk?.code_snippet || "";
};

const getRiskRefs = (risk: any, filePath?: string) => {
  const refs = Array.isArray(risk?.affected_files) ? risk.affected_files : [];
  return refs
    .map((ref: any) => (typeof ref === "string" ? { file_path: ref } : ref || {}))
    .filter((ref: any) => !filePath || ref.file_path === filePath);
};

const cleanRiskTitle = (value?: string) =>
  String(value || "Detected risk")
    .replace(/^fix:\s*/i, "")
    .trim();

const comparisonLine = (snippet?: string) =>
  String(snippet || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find((line) => line.includes("==")) || "";

const splitEquality = (line: string) => {
  const normalized = line
    .replace(/^(if|while)\s*\(/, "")
    .replace(/\)\s*\{?\s*$/, "")
    .trim();
  const parts = normalized.split("==");
  if (parts.length < 2) return null;
  return {
    left: parts[0].trim(),
    right: parts.slice(1).join("==").trim(),
  };
};

const deriveStringRisk = (risk: any, filePath?: string) => {
  const line = comparisonLine(getRiskSnippet(risk, filePath));
  const comparison = splitEquality(line);
  if (!comparison) return risk;

  const { left, right } = comparison;
  if (left === "null" || right === "null") return null;

  const literal = /^"(?:\\.|[^"\\])*"$/.test(right) ? right : /^"(?:\\.|[^"\\])*"$/.test(left) ? left : "";
  const expression = literal === right ? left : literal === left ? right : left;
  const literalValue = literal.replace(/^"|"$/g, "");

  if (literalValue === "") {
    return {
      ...risk,
      title: "Empty text compared with ==",
      description: `${expression} is compared to an empty string with ==, so the condition can fail even when the text is empty.`,
      recommendation: `Use ${expression}.isEmpty() or ${expression}.equals("") after any needed null check.`,
    };
  }

  if (line.includes("getSelectedItem()") && literal) {
    return {
      ...risk,
      title: "Selected item text compared with ==",
      description: `${expression} is compared with ==, which checks object identity instead of the selected text value.`,
      recommendation: `Use ${literal}.equals(String.valueOf(${expression})) so the selected item is compared by text.`,
    };
  }

  if (line.includes("getText()") && literal) {
    return {
      ...risk,
      title: "UI text compared with ==",
      description: `${expression} is compared with ==, which checks String object identity instead of UI text content.`,
      recommendation: `Use ${literal}.equals(${expression}) or Objects.equals(${expression}, ${literal}).`,
    };
  }

  return {
    ...risk,
    title: "String content compared with ==",
    description: `${left} and ${right} are compared with ==, so Java checks object identity instead of text content.`,
    recommendation: "Use .equals(...) or Objects.equals(...) for this exact comparison.",
  };
};

const displayRiskForFile = (risk: any, filePath?: string) => {
  const title = cleanRiskTitle(risk?.title).toLowerCase();
  const category = String(risk?.category || "").toLowerCase();
  const line = comparisonLine(getRiskSnippet(risk, filePath));
  const looksLikeOldStringFinding = title.includes("string comparison uses ==") || title.includes("string content compared");
  if ((looksLikeOldStringFinding || category === "logic_bug") && line.includes("==")) {
    return deriveStringRisk(risk, filePath);
  }
  return risk;
};

const collectKnownPaths = (results: any): string[] => {
  const values = new Set<string>();

  results?.metadata?.file_inventory?.forEach((file: any) => {
    if (file?.file_path) values.add(String(file.file_path));
  });

  results?.architecture?.entry_points?.forEach((entry: any) => {
    if (entry?.file_path) values.add(String(entry.file_path));
  });

  results?.risks?.forEach((risk: any) => {
    risk?.affected_files?.forEach((file: any) => {
      if (file?.file_path) values.add(String(file.file_path));
    });
  });

  results?.suggestions?.forEach((suggestion: any) => {
    suggestion?.affected_files?.forEach((file: any) => {
      if (file?.file_path) values.add(String(file.file_path));
    });
  });

  return Array.from(values).sort();
};

const buildFileTree = (paths: string[]): TreeNode[] => {
  const root: TreeNode[] = [];

  paths.forEach((originalPath) => {
    const normalized = originalPath.replace(/\\/g, "/").replace(/^[A-Za-z]:\//, "");
    const parts = normalized.split("/").filter(Boolean);
    let level = root;
    let currentPath = "";

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part;
      let node = level.find((item) => item.name === part);
      if (!node) {
        node = {
          name: part,
          path: currentPath,
          children: [],
          isFile: index === parts.length - 1,
        };
        level.push(node);
      }
      if (index === parts.length - 1) {
        node.isFile = true;
      }
      level = node.children;
    });
  });

  const sortNodes = (nodes: TreeNode[]) => {
    nodes.sort((a, b) => {
      if (!!a.isFile === !!b.isFile) return a.name.localeCompare(b.name);
      return a.isFile ? 1 : -1;
    });
    nodes.forEach((node) => sortNodes(node.children));
  };

  sortNodes(root);
  return root;
};

const renderSuggestionFallbacks = (results: any) => {
  const backendSuggestions = (results?.suggestions || []).map((suggestion: any) => ({
    ...suggestion,
    source: "backend",
  }));

  if (backendSuggestions.length) {
    return backendSuggestions;
  }

  const riskSuggestions = (results?.risks || []).slice(0, 6).map((risk: any) => ({
    suggestion_id: `risk-${risk.risk_id}`,
    title: `Resolve ${risk.title}`,
    description:
      risk.recommendation ||
      `Reduce ${risk.category || "codebase"} risk by addressing the conditions behind ${risk.title.toLowerCase()}.`,
    priority: risk.severity || "medium",
    estimated_effort: effortBySeverity[risk.severity] || "medium",
    category: risk.category || "risk",
    benefits: [
      `Lowers ${risk.severity || "medium"} operational exposure`,
      "Improves maintainability for future modernization work",
    ],
    risks: [],
    implementation_guide:
      risk.recommendation || "Investigate the affected modules, isolate the cause, and implement a tested remediation plan.",
    source: "llm-rendered",
  }));

  const roadmapSuggestions = (results?.recommended_next_steps || []).slice(0, 3).map((step: string, index: number) => ({
    suggestion_id: `next-step-${index}`,
    title: toTitle(step),
    description: step,
    priority: index === 0 ? "high" : "medium",
    estimated_effort: index === 0 ? "medium" : "low",
    category: "roadmap",
    benefits: ["Creates forward momentum", "Turns analysis into an execution plan"],
    risks: [],
    implementation_guide: step,
    source: "llm-rendered",
  }));

  return [...riskSuggestions, ...roadmapSuggestions];
};

const renderDependencyOverview = (results: any): DependencyOverview => {
  const graph = results?.architecture?.dependency_graph || { nodes: [], edges: [] };
  const architecture = results?.architecture || {};
  const risks = results?.risks || [];
  const frameworks = architecture.detected_frameworks || [];
  const layers = Object.keys(architecture.layers || {});
  const entryPoints = (architecture.entry_points || []).map((item: any) => item.file_path);
  const graphNodes = Array.isArray(graph.nodes) ? graph.nodes : [];
  const graphEdges = Array.isArray(graph.edges)
    ? graph.edges
        .map((edge: any) => ({
          from: edge.from ?? edge.source,
          to: edge.to ?? edge.target,
          label: edge.label ?? edge.type,
          weight: edge.weight,
        }))
        .filter((edge: any) => edge.from && edge.to)
    : [];

  if (graphNodes.length || graphEdges.length) {
    const structuralGraph = graphEdges.length ? null : buildStructuralDependencyMap(graphNodes);
    const visualNodes = structuralGraph?.nodes || graphNodes;
    const visualEdges = structuralGraph?.edges || graphEdges;

    return {
      nodes: visualNodes,
      edges: visualEdges,
      summary: graphEdges.length
        ? `Mapped ${graphNodes.length} dependency nodes and ${graphEdges.length} relationships from the analyzed codebase.`
        : `Mapped ${graphNodes.length} dependency nodes. No explicit import edges were returned, so the visual map is grouped by file structure.`,
      mode: graphEdges.length ? "graph" : "file map",
      totalNodes: graphNodes.length,
      totalEdges: graphEdges.length,
    };
  }

  const syntheticNodes = [
    ...entryPoints.slice(0, 4).map((path: string) => ({ id: path, label: path.split("/").pop(), type: "entry" })),
    ...layers.map((layer: string) => ({ id: layer, label: toTitle(layer), type: "layer" })),
    ...frameworks.slice(0, 4).map((framework: string) => ({ id: framework, label: framework, type: "framework" })),
    ...Array.from(new Set(risks.map((risk: any) => risk.category).filter(Boolean))).slice(0, 4).map((category: string) => ({
      id: category,
      label: toTitle(category),
      type: "risk",
    })),
  ];

  const syntheticEdges = [];
  if (entryPoints.length && layers.length) {
    syntheticEdges.push({ from: entryPoints[0], to: layers[0], label: "entry flow" });
  }
  if (layers.length > 1) {
    layers.forEach((layer: string, index: number) => {
      if (layers[index + 1]) {
        syntheticEdges.push({ from: layer, to: layers[index + 1], label: "depends on" });
      }
    });
  }
  if (layers.length && frameworks.length) {
    syntheticEdges.push({ from: frameworks[0], to: layers[0], label: "supports" });
  }

  const summaryParts = [
    architecture.project_type ? `${toTitle(architecture.project_type)} architecture` : null,
    frameworks.length ? `${frameworks.length} detected framework${frameworks.length > 1 ? "s" : ""}` : null,
    layers.length ? `${layers.length} logical layer${layers.length > 1 ? "s" : ""}` : null,
    risks.length ? `${risks.length} risk signal${risks.length > 1 ? "s" : ""} shaping the dependency story` : null,
  ].filter(Boolean);

  return {
    nodes: syntheticNodes,
    edges: syntheticEdges,
    summary: summaryParts.length
      ? `${summaryParts.join(", ")}. Rendered from architecture and risk context while the backend graph is still sparse.`
      : "Rendered a dependency overview from the available architecture and risk context.",
    mode: "synthesized",
    totalNodes: syntheticNodes.length,
    totalEdges: syntheticEdges.length,
  };
};

const FileTree = ({ nodes, depth = 0 }: { nodes: TreeNode[]; depth?: number }) => (
  <div className="space-y-1">
    {nodes.map((node) => (
      <Fragment key={node.path}>
        <div
          className="flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent/60"
          style={{ paddingLeft: `${depth * 16 + 12}px` }}
        >
          <span className={node.isFile ? "text-foreground/90" : "font-medium"}>{node.name}</span>
          {!node.isFile && <Badge variant="secondary">{node.children.length}</Badge>}
        </div>
        {node.children.length > 0 && <FileTree nodes={node.children} depth={depth + 1} />}
      </Fragment>
    ))}
  </div>
);

const DependencyGraphCanvas = ({ overview }: { overview: DependencyOverview }) => {
  const width = 760;
  const height = 420;
  const centerX = width / 2;
  const nodeRadius = 18;
  const nodes = overview.nodes.slice(0, 42);
  const positions = new Map<string, { x: number; y: number }>();
  const visibleNodeIds = new Set(nodes.map((node) => node.id));
  const edges = overview.edges.filter((edge) => visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to)).slice(0, 56);

  const childrenByParent = new Map<string, string[]>();
  const incoming = new Set<string>();
  edges.forEach((edge) => {
    childrenByParent.set(edge.from, [...(childrenByParent.get(edge.from) || []), edge.to]);
    incoming.add(edge.to);
  });

  const roots = nodes.filter((node) => !incoming.has(node.id));
  const primaryRoot = nodes.find((node) => node.id === "root") || roots[0] || nodes[0];
  const levels = new Map<string, number>();
  const queue = primaryRoot ? [{ id: primaryRoot.id, level: 0 }] : [];

  while (queue.length) {
    const current = queue.shift();
    if (!current || levels.has(current.id)) continue;
    levels.set(current.id, current.level);
    (childrenByParent.get(current.id) || []).forEach((childId) => {
      queue.push({ id: childId, level: current.level + 1 });
    });
  }

  nodes.forEach((node) => {
    if (!levels.has(node.id)) {
      levels.set(node.id, Math.min(levels.size % 5, 4));
    }
  });

  const nodesByLevel = new Map<number, DependencyGraphNode[]>();
  nodes.forEach((node) => {
    const level = Math.min(levels.get(node.id) || 0, 5);
    nodesByLevel.set(level, [...(nodesByLevel.get(level) || []), node]);
  });

  const orderedLevels = Array.from(nodesByLevel.keys()).sort((a, b) => a - b);
  orderedLevels.forEach((level, levelIndex) => {
    const levelNodes = nodesByLevel.get(level) || [];
    const y = 48 + levelIndex * ((height - 96) / Math.max(orderedLevels.length - 1, 1));
    const gap = width / (levelNodes.length + 1);
    levelNodes.forEach((node, index) => {
      positions.set(node.id, {
        x: Math.max(42, Math.min(width - 42, gap * (index + 1))),
        y,
      });
    });
  });

  return (
    <div className="overflow-hidden rounded-md border bg-background/60">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Dependency graph" className="h-[420px] w-full">
        <defs>
          <marker id="dependency-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" className="fill-muted-foreground" />
          </marker>
        </defs>

        {edges.map((edge, index) => {
          const from = positions.get(edge.from);
          const to = positions.get(edge.to);
          if (!from || !to) return null;
          const midY = (from.y + to.y) / 2;
          const path = `M ${from.x} ${from.y + nodeRadius} C ${from.x} ${midY}, ${to.x} ${midY}, ${to.x} ${to.y - nodeRadius - 4}`;

          return (
            <g key={`${edge.from}-${edge.to}-${index}`}>
              <path
                d={path}
                className="fill-none stroke-muted-foreground/55"
                strokeWidth="1.4"
                markerEnd="url(#dependency-arrow)"
              />
            </g>
          );
        })}

        {nodes.map((node) => {
          const position = positions.get(node.id) || { x: centerX, y: 48 };
          const label = nodeLabel(node);
          const isFolder = node.type === "folder" || node.type === "root";
          const fill = isFolder ? "fill-[#f1d08a]" : "fill-[#a7e3cf]";
          const stroke = isFolder ? "stroke-[#d8a94e]" : "stroke-[#73c8b3]";
          return (
            <g key={node.id}>
              <circle cx={position.x} cy={position.y} r={nodeRadius} className={`${fill} ${stroke}`} strokeWidth="1.5" />
              <text x={position.x} y={position.y + 34} textAnchor="middle" className="fill-foreground text-[11px] font-semibold">
                {label.length > 18 ? `${label.slice(0, 16)}...` : label}
              </text>
              <text x={position.x} y={position.y + 47} textAnchor="middle" className="fill-muted-foreground text-[9px]">
                {toTitle(node.type || "file")}
              </text>
            </g>
          );
        })}
      </svg>
      {overview.nodes.length > nodes.length && (
        <div className="border-t px-4 py-2 text-xs text-muted-foreground">
          Showing {nodes.length} of {overview.nodes.length} visual nodes to keep the map readable.
        </div>
      )}
    </div>
  );
};



const Analysis = () => {
  const { jobId = "" } = useParams();
  const status = useQuery({
    queryKey: ["job", jobId],
    queryFn: async () => (await analysisService.getJobStatus(jobId)).data,
    refetchInterval: (q) => {
      const state = q.state.data?.status;
      return state === "queued" || state === "processing" || state === "running" ? 2000 : false;
    },
    retry: false,
    enabled: !!jobId,
  });
  const isCompleted = status.data?.status === "completed";

  const results = useQuery({
    queryKey: ["results", jobId],
    queryFn: async () => (await analysisService.getResults(jobId)).data,
    enabled: isCompleted,
    retry: false,
  });



  const progress = status.data?.progress_percent ?? 0;
  const currentStageIdx = Math.min(Math.floor(progress / 20), STAGES.length - 1);
  const metadata = results.data?.metadata;
  const renderedSuggestions = renderSuggestionFallbacks(results.data);
  const filePaths = collectKnownPaths(results.data);
  const fileTree = buildFileTree(filePaths);
  const dependencyOverview = renderDependencyOverview(results.data);
  const architectureHighlights = [
    results.data?.architecture?.primary_language ? `Primary language: ${String(results.data.architecture.primary_language).toUpperCase()}` : null,
    results.data?.architecture?.project_type ? `Project type: ${toTitle(results.data.architecture.project_type)}` : null,
    results.data?.architecture?.detected_frameworks?.length ? `Frameworks: ${results.data.architecture.detected_frameworks.join(", ")}` : null,
  ].filter(Boolean);

  const jobList = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => (await analysisService.listJobs()).data,
  });
  const currentJob = jobList.data?.jobs?.find((j: any) => j.id === jobId);
  const projectName = currentJob?.project_name || (status.data as any)?.project_name || `Job ${jobId}`;

  return (
    <div className="mx-auto w-full max-w-7xl">
      <PageHeader
        title="Analysis"
        description={projectName}
        actions={
          <>
            <Button asChild variant="outline"><Link to={`/analysis/${jobId}/query`}>Ask</Link></Button>
            <Button asChild><Link to={`/analysis/${jobId}/report`}>Report</Link></Button>
          </>
        }
      />

      {!status.data && status.isError && (
        <EmptyState title="Job not found" description="We couldn't load this analysis. The backend may be unreachable." />
      )}

      {status.data && !isCompleted && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {status.data.status === "processing" || status.data.status === "running" ? "Analyzing your code..." : status.data.message}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Progress value={progress} className="h-2" />
            <div className="mt-2 flex items-center justify-between text-sm text-muted-foreground">
              <span>{status.data.current_stage || STAGES[currentStageIdx]}</span>
              <span>{progress}%</span>
            </div>
            <div className="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
              {(status.data.stages?.length ? status.data.stages.map((stage) => stage.stage_name) : STAGES).map((s, i) => (
                <div key={s} className={`rounded-md border px-2 py-2 text-center text-xs ${i <= currentStageIdx ? "border-primary/40 bg-accent text-accent-foreground" : "border-border bg-card text-muted-foreground"}`}>
                  <div className="font-semibold">{String(i + 1).padStart(2, "0")}</div>
                  <div>{s}</div>
                </div>
              ))}
            </div>
            <div className="mt-6 flex justify-end">
              <Button variant="outline" onClick={() => analysisService.cancelJob(jobId)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {isCompleted && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: "Files", value: metadata?.total_files ?? filePaths.length ?? 0 },
              { label: "Lines of code", value: metadata?.total_lines_of_code },
              { label: "Risks", value: results.data?.risks?.length },
            ].map((c) => (
              <Card key={c.label}>
                <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">{c.label}</CardTitle></CardHeader>
                <CardContent><div className="text-2xl font-bold">{c.value ?? "--"}</div></CardContent>
              </Card>
            ))}
          </div>

          <Tabs defaultValue="risks" className="mt-8">
            <TabsList className="w-full flex justify-start overflow-x-auto">
              <TabsTrigger value="risks">Risks</TabsTrigger>
              <TabsTrigger value="files">Files</TabsTrigger>
              <TabsTrigger value="graph">Dependencies</TabsTrigger>
            </TabsList>

            <TabsContent value="risks" className="mt-4">
              {results.data?.risks?.length ? (() => {
                /* Group risks by file path for file → line → issue layout */
                const risksByFile: Record<string, any[]> = {};
                results.data.risks.forEach((r: any, i: number) => {
                  const files = r.affected_files?.length
                    ? r.affected_files.map((f: any) => (typeof f === "string" ? f : f?.file_path || "unknown"))
                    : ["(project-wide)"];
                  files.forEach((fp: string) => {
                    if (!risksByFile[fp]) risksByFile[fp] = [];
                    const displayRisk = displayRiskForFile(r, fp);
                    if (displayRisk) risksByFile[fp].push({ ...displayRisk, _idx: i });
                  });
                });

                /* Sort files: most issues first */
                const sortedFiles = Object.entries(risksByFile).sort((a, b) => b[1].length - a[1].length);
                const visibleRisks = Object.values(risksByFile).flat();

                /* Severity summary */
                const counts = { critical: 0, high: 0, medium: 0, low: 0 };
                visibleRisks.forEach((r: any) => {
                  const s = (r.severity || "").toLowerCase();
                  if (s in counts) counts[s as keyof typeof counts]++;
                });

                return (
                  <div className="space-y-6">
                    {/* Summary bar */}
                    <div className="grid gap-3 sm:grid-cols-4">
                      {(["critical", "high", "medium", "low"] as const).map((sev) => (
                        <div key={sev} className="rounded-md border bg-card p-3 text-center">
                          <div className="text-xs uppercase text-muted-foreground">{sev}</div>
                          <div className={`mt-1 text-xl font-bold ${
                            sev === "critical" || sev === "high" ? "text-destructive" :
                            sev === "medium" ? "text-warning" : "text-success"
                          }`}>{counts[sev]}</div>
                        </div>
                      ))}
                    </div>

                    {/* File-grouped issues — compact error list */}
                    {sortedFiles.map(([filePath, fileRisks]) => (
                      <div key={filePath} className="space-y-3">
                        <h3 className="font-semibold text-base flex items-center gap-2 border-b pb-2">
                          {filePath}
                          <Badge variant="outline" className="ml-auto text-xs">
                            {fileRiskLabel(results.data?.metadata?.file_risk?.[filePath])}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">{fileRisks.length} Issue{fileRisks.length > 1 ? "s" : ""}</Badge>
                        </h3>

                        <div className="space-y-3">
                          {fileRisks
                            .sort((a: any, b: any) => {
                              const lineDiff = ((getRiskLine(a, filePath) || 0) - (getRiskLine(b, filePath) || 0));
                              if (lineDiff !== 0) return lineDiff;
                              return (priorityRank[b.severity] || 0) - (priorityRank[a.severity] || 0);
                            })
                            .map((r: any, riskIndex: number) => {
                              const lineNum = getRiskLine(r, filePath);
                              const refs = getRiskRefs(r, filePath);
                              const instances = refs.length ? refs : [{ line_start: lineNum, snippet: getRiskSnippet(r, filePath) }];
                              const sortedInstances = instances
                                .filter((ref: any) => ref?.line_start || ref?.snippet || ref?.code_snippet)
                                .sort((a: any, b: any) => (a.line_start || 0) - (b.line_start || 0));
                              return (
                                <Card
                                  key={`${filePath}-${r.risk_id || r.title}-${lineNum ?? "no-line"}-${r._idx}-${riskIndex}`}
                                  className="overflow-hidden border-l-4 border-l-primary"
                                >
                                  <CardContent className="p-0">
                                    <div className="bg-muted/50 px-4 py-2 flex flex-col gap-2 border-b sm:flex-row sm:items-center sm:justify-between">
                                      <div className="flex flex-wrap items-center gap-2">
                                  <Badge className={`text-[10px] px-1.5 py-0 shrink-0 ${severityColor[r.severity] || severityColor.info}`}>
                                    {(r.severity || "?").toUpperCase()}
                                  </Badge>
                                  <span className="hidden">
                                    {lineNum !== null ? `L${lineNum}` : "—"}
                                  </span>
                                  <Badge variant="secondary" className="text-xs">{toTitle(r.category || "general")}</Badge>
                                  <Badge variant="outline" className="text-xs">
                                    {sortedInstances.length || 1} instance{(sortedInstances.length || 1) > 1 ? "s" : ""}
                                  </Badge>
                                  </div>
                                  <span className="text-sm font-semibold">{cleanRiskTitle(r.title)}</span>
                                  </div>

                                  <div className="max-h-[900px] overflow-y-auto p-4 space-y-4 custom-scrollbar">
                                    <div className="grid gap-4 md:grid-cols-2">
                                      {r.description && (
                                        <div className="space-y-1">
                                          <h4 className="text-sm font-medium text-muted-foreground">Risk</h4>
                                          <p className="text-sm text-muted-foreground leading-relaxed">{r.description}</p>
                                        </div>
                                      )}
                                      {r.recommendation && (
                                        <div className="space-y-1">
                                          <h4 className="text-sm font-medium text-muted-foreground">Fix</h4>
                                          <p className="text-sm text-muted-foreground leading-relaxed">{r.recommendation}</p>
                                        </div>
                                      )}
                                    </div>

                                    {sortedInstances.length ? (
                                      <div className="space-y-2">
                                        <h4 className="text-sm font-medium text-muted-foreground">Affected instances</h4>
                                        <div className="rounded-md border bg-zinc-950/20 p-1">
                                            {sortedInstances.map((ref: any, instanceIndex: number) => {
                                              const instanceSnippet = ref?.snippet || ref?.code_snippet || "";
                                              return (
                                                <div key={`${filePath}-${r.risk_id || r.title}-instance-${ref?.line_start || "x"}-${instanceIndex}`} className="grid gap-1.5 p-2 md:grid-cols-[100px_1fr]">
                                                  <div className="font-mono text-[10px] text-muted-foreground pt-1">
                                                    Line {ref?.line_start ?? "-"}
                                                    {ref?.line_end && ref.line_end !== ref.line_start ? `-${ref.line_end}` : ""}
                                                  </div>
                                                  {instanceSnippet ? (
                                                    <pre className="w-full overflow-x-auto rounded bg-zinc-950 px-2 py-1.5 text-[10px] text-zinc-50 leading-tight">
                                                      <code>{instanceSnippet}</code>
                                                    </pre>
                                                  ) : (
                                                    <span className="text-sm text-muted-foreground">No snippet returned for this instance.</span>
                                                  )}
                                                </div>
                                              );
                                            })}
                                          </div>
                                        </div>
                                      ) : null}
                                  </div>
                                  </CardContent>
                                </Card>
                              );
                            })}
                        </div>
                      </div>
                    ))}
                  </div>
                );
              })() : (
                <EmptyState title="No risks reported" description="Risk findings will appear here once the analysis returns data." />
              )}
            </TabsContent>

            <TabsContent value="suggestions" className="mt-4">
              {renderedSuggestions.length ? (() => {
                /* Group suggestions by file path */
                const sugsByFile: Record<string, any[]> = {};
                renderedSuggestions.forEach((s: any, i: number) => {
                  const files = s.affected_files?.length
                    ? s.affected_files.map((f: any) => (typeof f === "string" ? f : f?.file_path || "unknown"))
                    : ["(project-wide)"];
                  files.forEach((fp: string) => {
                    if (!sugsByFile[fp]) sugsByFile[fp] = [];
                    const key = `${s.title || ""}|${s.description || ""}|${s.implementation_guide || ""}`;
                    const exists = sugsByFile[fp].some((item: any) => item._dedupeKey === key);
                    if (!exists) sugsByFile[fp].push({ ...s, _idx: i, _dedupeKey: key });
                  });
                });

                const sortedFiles = Object.entries(sugsByFile).sort((a, b) => b[1].length - a[1].length);

                /* Priority summary */
                const counts = { critical: 0, high: 0, medium: 0, low: 0 };
                renderedSuggestions.forEach((s: any) => {
                  const p = (s.priority || "").toLowerCase();
                  if (p in counts) counts[p as keyof typeof counts]++;
                });

                return (
                  <div className="space-y-6">
                    {/* Summary bar */}
                    <div className="grid gap-3 sm:grid-cols-4">
                      {(["critical", "high", "medium", "low"] as const).map((pri) => (
                        <div key={pri} className="rounded-md border bg-card p-3 text-center">
                          <div className="text-xs uppercase text-muted-foreground">{pri}</div>
                          <div className={`mt-1 text-xl font-bold ${
                            pri === "critical" || pri === "high" ? "text-primary" :
                            pri === "medium" ? "text-warning" : "text-muted-foreground"
                          }`}>{counts[pri]}</div>
                        </div>
                      ))}
                    </div>

                    {/* File-grouped suggestions */}
                    {sortedFiles.map(([filePath, fileSugs]) => (
                      <div key={filePath} className="space-y-3">
                        <h3 className="font-semibold text-base flex items-center gap-2 border-b pb-2">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          {filePath}
                          <Badge variant="secondary" className="ml-auto">{fileSugs.length} suggestion{fileSugs.length > 1 ? "s" : ""}</Badge>
                        </h3>

                        <div className="space-y-3">
                          {fileSugs
                            .sort((a: any, b: any) => (priorityRank[b.priority] || 0) - (priorityRank[a.priority] || 0))
                            .map((s: any, suggestionIndex: number) => {
                              const lineNum = s.line_start || s.line || null;
                              const guide = String(s.implementation_guide || s.fix || "").trim();
                              const showGuide = guide && !guide.toLowerCase().startsWith("derived from");
                              return (
                                <Card key={`${filePath}-${s.suggestion_id || s.title}-${s._idx}-${suggestionIndex}`} className={`overflow-hidden border-l-4 ${
                                  s.priority === "critical" || s.priority === "high" ? "border-l-primary" :
                                  s.priority === "medium" ? "border-l-warning" : "border-l-muted-foreground"
                                }`}>
                                  <CardContent className="p-0">
                                    {/* Header row */}
                                    <div className="bg-muted/50 px-4 py-2 flex flex-col sm:flex-row sm:items-center justify-between border-b gap-2">
                                      <div className="flex flex-wrap items-center gap-2">
                                        <Badge variant="outline" className={
                                          s.priority === "critical" || s.priority === "high" ? "text-primary border-primary/50" :
                                          s.priority === "medium" ? "text-warning border-warning/50" : "text-muted-foreground border-border"
                                        }>
                                          {(s.priority || "medium").toUpperCase()}
                                        </Badge>
                                        {lineNum !== null && (
                                          <span className="text-sm font-medium whitespace-nowrap">Line {lineNum}</span>
                                        )}
                                        <Badge variant="secondary" className="text-xs">{toTitle(s.estimated_effort || "medium")} effort</Badge>
                                      </div>
                                      <span className="text-sm font-semibold">{s.title}</span>
                                    </div>

                                    <div className="max-h-[500px] overflow-y-auto p-4 space-y-3 custom-scrollbar">
                                      {/* Code snippet if available */}
                                      {s.code_snippet && (
                                        <div className="rounded-md bg-zinc-950 p-3 overflow-x-auto">
                                          <pre className="text-sm text-zinc-50 font-mono"><code>{s.code_snippet}</code></pre>
                                        </div>
                                      )}

                                      {/* Problem + Fix side-by-side */}
                                      <div className="grid gap-4 md:grid-cols-2">
                                        <div className="space-y-1">
                                          <h4 className="text-sm font-medium text-muted-foreground">What to change</h4>
                                          <p className="text-sm text-muted-foreground leading-relaxed">{s.description}</p>
                                        </div>
                                        {showGuide && (
                                          <div className="space-y-1">
                                            <h4 className="text-sm font-medium text-muted-foreground">Action</h4>
                                            <p className="text-sm text-muted-foreground leading-relaxed">{guide}</p>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  </CardContent>
                                </Card>
                              );
                            })}
                        </div>
                      </div>
                    ))}
                  </div>
                );
              })() : (
                <EmptyState title="No suggestions yet" description="Modernization suggestions will appear here." />
              )}
            </TabsContent>

            <TabsContent value="files" className="mt-4">
              {fileTree.length ? (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Rendered file map</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                      File references were reconstructed from architecture entry points, risk references, and suggestion context to give us a usable map even when the backend does not return a full inventory tree yet.
                    </p>
                    <ScrollArea className="h-[420px] rounded-md border">
                      <div className="p-3 pr-6">
                        <FileTree nodes={fileTree} />
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              ) : (
                <EmptyState title="File explorer" description="No file paths were included in the current analysis payload yet." />
              )}
            </TabsContent>

            <TabsContent value="graph" className="mt-4">
              <div className="grid gap-4 lg:grid-cols-[1.3fr_0.9fr]">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Dependency rendering</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground">{dependencyOverview.summary}</p>
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div className="rounded-md border bg-accent/40 p-4">
                        <div className="text-xs uppercase text-muted-foreground">Nodes</div>
                        <div className="mt-1 text-2xl font-semibold">{dependencyOverview.totalNodes}</div>
                      </div>
                      <div className="rounded-md border bg-accent/40 p-4">
                        <div className="text-xs uppercase text-muted-foreground">Edges</div>
                        <div className="mt-1 text-2xl font-semibold">{dependencyOverview.totalEdges}</div>
                      </div>
                      <div className="rounded-md border bg-accent/40 p-4">
                        <div className="text-xs uppercase text-muted-foreground">Mode</div>
                        <div className="mt-1 text-sm font-semibold">{toTitle(dependencyOverview.mode)}</div>
                      </div>
                    </div>
                    {dependencyOverview.nodes.length ? (
                      <DependencyGraphCanvas overview={dependencyOverview} />
                    ) : null}
                    <div className="space-y-3">
                      {dependencyOverview.edges.length ? (
                        <div className="overflow-hidden rounded-md border">
                          <div className="grid grid-cols-[1.2fr_130px_1.2fr] border-b bg-muted/40 px-3 py-2 text-xs font-semibold uppercase text-muted-foreground">
                            <div>Source</div>
                            <div>Relationship</div>
                            <div>Target</div>
                          </div>
                          <ScrollArea className="max-h-96">
                            <div className="divide-y divide-border/70 pr-3">
                              {dependencyOverview.edges.slice(0, 80).map((edge: any, index: number) => (
                                <div key={`${edge.from}-${edge.to}-${index}`} className="grid grid-cols-[1.2fr_130px_1.2fr] items-center gap-3 px-3 py-2 text-sm">
                                  <div className="flex min-w-0 items-center gap-2">
                                    <GitBranch className="h-4 w-4 shrink-0 text-primary" />
                                    <span className="truncate font-medium" title={edge.from}>{basename(edge.from)}</span>
                                  </div>
                                  <Badge variant="outline" className="w-fit max-w-full truncate">{edgeLabel(edge)}</Badge>
                                  <span className="truncate text-muted-foreground" title={edge.to}>{basename(edge.to)}</span>
                                </div>
                              ))}
                            </div>
                          </ScrollArea>
                          {dependencyOverview.edges.length > 80 && (
                            <div className="border-t px-3 py-2 text-xs text-muted-foreground">
                              Showing 80 of {dependencyOverview.edges.length} relationships.
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
                          No explicit dependency edges came back from the backend yet. The graph above shows the analyzed module as an isolated node.
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Architecture context</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                      {architectureHighlights.length ? architectureHighlights.map((item, index) => (
                       <div key={`${item}-${index}`} className="rounded-md border p-3 text-sm">{item}</div>
                    )) : (
                      <div className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
                        The backend returned only a minimal architecture snapshot for this run.
                      </div>
                    )}
                    {results.data?.migration_blockers?.length ? (
                      <div className="rounded-md border p-3">
                        <div className="mb-2 text-sm font-medium">Migration blockers</div>
                        <div className="flex flex-wrap gap-2">
                           {results.data.migration_blockers.map((blocker: string, index: number) => (
                             <Badge key={`${blocker}-${index}`} variant="secondary">{blocker}</Badge>
                           ))}
                        </div>
                      </div>
                    ) : null}
                    {results.data?.recommended_next_steps?.length ? (
                      <div className="rounded-md border p-3">
                        <div className="mb-2 text-sm font-medium">Recommended next steps</div>
                        <div className="space-y-2 text-sm text-muted-foreground">
                          {results.data.recommended_next_steps.map((step: string, si: number) => (
                            <p key={`next-step-${si}`}>{step}</p>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
};

export default Analysis;
