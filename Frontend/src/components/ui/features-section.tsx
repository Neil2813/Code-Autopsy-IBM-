import { Activity, DraftingCompass, Mail, Zap, Code, Shield, Search, Network } from 'lucide-react'

export function FeaturesSection() {
    return (
        <section className="py-16 md:py-32 bg-[#000000] text-white">
            <div className="mx-auto max-w-xl md:max-w-6xl px-6">
                <div className="grid items-center gap-12 md:grid-cols-2 md:gap-12 lg:grid-cols-5 lg:gap-24">
                    <div className="lg:col-span-2">
                        <div className="md:pr-6 lg:pr-0">
                            <h2 className="text-4xl font-bold lg:text-5xl tracking-tight font-heading">
                                Built for Enterprise <span className="text-primary">Legacy Modernization</span>
                            </h2>
                            <p className="mt-6 text-zinc-400 leading-relaxed">
                                Accelerate your transformation journey with AI-driven insights. From mainframe COBOL to modern Java architectures, we handle the complexity so your team can focus on innovation.
                            </p>
                        </div>
                        <ul className="mt-8 divide-y border-y border-white/10 *:flex *:items-center *:gap-3 *:py-4 text-sm md:text-base">
                            <li className="group hover:bg-white/5 transition-colors px-2 rounded-lg">
                                <Search className="size-5 text-primary" />
                                <span>Deep Codebase Diagnostics</span>
                            </li>
                            <li className="group hover:bg-white/5 transition-colors px-2 rounded-lg">
                                <Zap className="size-5 text-primary" />
                                <span>AI-Powered Modernization Plans</span>
                            </li>
                            <li className="group hover:bg-white/5 transition-colors px-2 rounded-lg">
                                <Activity className="size-5 text-primary" />
                                <span>Risk & Complexity Scoring</span>
                            </li>
                            <li className="group hover:bg-white/5 transition-colors px-2 rounded-lg">
                                <Network className="size-5 text-primary" />
                                <span>Interactive Architecture Mapping</span>
                            </li>
                        </ul>
                    </div>
                    <div className="border-white/10 relative rounded-3xl border p-3 lg:col-span-3 bg-zinc-900/20 backdrop-blur-sm">
                        <div className="bg-gradient-to-b aspect-[76/59] relative rounded-2xl from-zinc-800 to-transparent p-px overflow-hidden">
                            <img 
                                src="https://images.unsplash.com/photo-1555066931-4365d14bab8c?q=80&w=2070&auto=format&fit=crop" 
                                className="w-full h-full object-cover rounded-[15px] opacity-80" 
                                alt="Code modernizing illustration" 
                                width={1207} 
                                height={929} 
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                        </div>
                    </div>
                </div>
            </div>
        </section>
    )
}
