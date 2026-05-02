import { Button } from "@/components/ui/button";
import { HeroSection } from "@/components/ui/3d-hero-section-boxes";
import { FeaturesSection } from "@/components/ui/features-section";
import { CtaSection } from "@/components/ui/cta-section";


const Index = () => (
  <div className="bg-[#000000] min-h-screen text-white">
    <HeroSection />

    {/* Welcome Message */}
    <section className="container py-24 flex flex-col items-center justify-center text-center">
      <div className="relative group">
        <div className="absolute -inset-4 bg-gradient-to-r from-primary/50 to-blue-600/50 rounded-full blur-2xl opacity-20 group-hover:opacity-40 transition duration-1000"></div>
        <div className="relative p-1 rounded-full bg-gradient-to-b from-white/10 to-transparent">
          <img 
            src="/chatbot.png" 
            alt="Chatbot" 
            className="w-40 h-40 md:w-56 md:h-56 object-contain rounded-full bg-black/40 backdrop-blur-xl"
          />
        </div>
      </div>
      <h2 className="mt-10 text-4xl md:text-6xl font-black tracking-tight font-heading">
        <span className="block text-white">CODE AUTOPSY</span>
        <span className="block mt-2 bg-clip-text text-transparent bg-gradient-to-r from-primary to-blue-400">WELCOMES YOU</span>
      </h2>
      <div className="mt-8 w-24 h-1 bg-primary rounded-full mx-auto opacity-50"></div>
    </section>

    <FeaturesSection />

    <CtaSection />
  </div>
);

export default Index;
