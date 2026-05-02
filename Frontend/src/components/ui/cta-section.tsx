import { ArrowRight, Check } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

interface CtaSectionProps {
  title?: string;
  description?: string;
  buttonText?: string;
  buttonUrl?: string;
  items?: string[];
}

const defaultItems = [
  "Deep Java & COBOL Analysis",
  "Automated Risk Scoring",
  "Interactive Dependency Graphs",
  "AI Modernization Roadmaps",
  "Executive-Ready Reports",
];

export const CtaSection = ({
  title = "Ship Modernization, Not Migrations",
  description = "Get a complete picture of your legacy estate with one upload. Our AI agents guide you through every step of the modernization process.",
  buttonText = "Get Started Now",
  buttonUrl = "/register",
  items = defaultItems,
}: CtaSectionProps) => {
  return (
    <section className="py-24 md:py-32 bg-[#000000]">
      <div className="container mx-auto px-4">
        <div className="flex justify-center">
          <div className="max-w-5xl w-full">
            <div className="flex flex-col items-start justify-between gap-12 rounded-3xl bg-zinc-900/40 border border-white/10 px-8 py-12 md:flex-row lg:px-20 lg:py-16 backdrop-blur-sm shadow-2xl">
              <div className="md:w-3/5">
                <h4 className="mb-4 text-3xl font-bold md:text-5xl tracking-tight text-white font-heading leading-tight">
                  {title}
                </h4>
                <p className="text-zinc-400 text-lg leading-relaxed">
                  {description}
                </p>
                <Button className="mt-8 h-14 px-10 rounded-full text-base font-bold shadow-lg shadow-primary/20" asChild>
                  <Link to={buttonUrl}>
                    {buttonText} <ArrowRight className="ml-2 size-5" />
                  </Link>
                </Button>
              </div>
              <div className="md:w-2/5 w-full">
                <ul className="flex flex-col space-y-4 text-sm md:text-base font-medium text-zinc-300">
                  {items.map((item, idx) => (
                    <li className="flex items-center group transition-colors hover:text-white" key={idx}>
                      <div className="mr-4 flex size-6 items-center justify-center rounded-full bg-primary/20 text-primary">
                        <Check className="size-4" />
                      </div>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
