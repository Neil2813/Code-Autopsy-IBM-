import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const About = () => (
  <div className="min-h-screen bg-[#000000] text-white">
    <div className="container max-w-4xl py-24">
      <PageHeader 
        title="About Code Autopsy" 
        description="An AI copilot for legacy modernization." 
      />
      <div className="grid gap-6 md:grid-cols-2 mt-12">
        <Card className="bg-zinc-900/50 border-white/10 text-white backdrop-blur-sm">
          <CardHeader><CardTitle className="text-xl font-bold">Mission</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-400 leading-relaxed">
            Help enterprises understand and modernize their legacy estates with AI-driven analysis and guidance.
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-white/10 text-white backdrop-blur-sm">
          <CardHeader><CardTitle className="text-xl font-bold">IBM watsonx.ai</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-400 leading-relaxed">
            We use watsonx.ai's foundation models for code understanding, classification and recommendation generation.
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-white/10 text-white backdrop-blur-sm">
          <CardHeader><CardTitle className="text-xl font-bold">Languages</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-400 leading-relaxed">
            Java, COBOL, RPG, PL/I, and more mainframe and enterprise languages.
          </CardContent>
        </Card>
        <Card className="bg-zinc-900/50 border-white/10 text-white backdrop-blur-sm">
          <CardHeader><CardTitle className="text-xl font-bold">Version</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-400 leading-relaxed">
            Code Autopsy v1.0 · Frontend shell
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
);

export default About;