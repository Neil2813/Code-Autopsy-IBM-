"use client";

import React, { useEffect, useRef } from 'react';
import Spline from '@splinetool/react-spline';
import { LayoutGrid, Code, Zap, Shield, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

function HeroSplineBackground() {
  return (
    <div style={{
      position: 'relative',
      width: '100%',
      height: '100vh',
      pointerEvents: 'auto',
      overflow: 'hidden',
    }}>
      <Spline
        style={{
          width: '100%',
          height: '100vh',
          pointerEvents: 'auto',
        }}
        scene="https://prod.spline.design/dJqTIQ-tE3ULUPMi/scene.splinecode"
      />
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100vh',
          background: `
            linear-gradient(to right, rgba(0, 0, 0, 0.9), transparent 30%, transparent 70%, rgba(0, 0, 0, 0.9)),
            linear-gradient(to bottom, transparent 50%, rgba(0, 0, 0, 1))
          `,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
}


function HeroContent() {
  return (
    <div className="text-white px-4 max-w-screen-xl mx-auto w-full flex flex-col lg:flex-row justify-between items-start lg:items-center py-16">

      <div className="w-full lg:w-1/2 pr-0 lg:pr-8 mb-8 lg:mb-0">
        <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-4 leading-tight tracking-wide font-heading">
          Uncover. Analyze.<br />Modernize.
        </h1>
        <div className="flex items-center gap-4 text-xs font-mono text-primary uppercase tracking-[0.2em] opacity-90 mt-6">
          <span className="flex items-center gap-1.5"><Code className="h-3.5 w-3.5" /> Java</span>
          <span className="w-1 h-1 rounded-full bg-white/20" />
          <span className="flex items-center gap-1.5"><Zap className="h-3.5 w-3.5" /> COBOL</span>
          <span className="w-1 h-1 rounded-full bg-white/20" />
          <span className="flex items-center gap-1.5"><Shield className="h-3.5 w-3.5" /> Mainframe</span>
        </div>
      </div>

      <div className="w-full lg:w-1/2 pl-0 lg:pl-8 flex flex-col items-start">
         <p className="text-base sm:text-lg text-gray-300 opacity-80 mb-8 max-w-md leading-relaxed">
           Deep codebase diagnostics and AI-powered modernization plans for enterprise legacy estates.
        </p>
        <div className="flex pointer-events-auto flex-col sm:flex-row items-start space-y-3 sm:space-y-0 sm:space-x-4">
             <Button asChild variant="outline" size="lg" className="border-white/60 text-white font-semibold py-6 px-8 rounded-2xl transition duration-300 w-full sm:w-auto hover:bg-white/10 hover:border-white/100">
                <Link to="/docs">Documentation</Link>
            </Button>
            <Button asChild size="lg" className="pointer-events-auto bg-primary hover:bg-primary/90 text-white font-semibold py-6 px-8 rounded-2xl transition duration-300 hover:scale-105 flex items-center justify-center w-full sm:w-auto shadow-lg shadow-primary/40">
               <Link to="/register" className="flex items-center text-white">
                 <Search className="w-4 h-4 sm:w-5 sm:h-5 mr-2 text-white" />
                 Start Free Analysis
               </Link>
            </Button>
        </div>
      </div>

    </div>
  );
}

const HeroSection = () => {
  const heroContentRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const handleScroll = () => {
      if (heroContentRef.current) {
        requestAnimationFrame(() => {
          const scrollPosition = window.pageYOffset;
          const maxScroll = 500;
          const opacity = 1 - Math.min(scrollPosition / maxScroll, 1);
          if (heroContentRef.current) {
             heroContentRef.current.style.opacity = opacity.toString();
             heroContentRef.current.style.transform = `translateY(${scrollPosition * 0.2}px)`;
          }
        });
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="relative bg-[#000000]">
      <div className="relative min-h-screen">
        <div className="absolute inset-0 z-0 pointer-events-auto">
          <HeroSplineBackground />
        </div>

        <div ref={heroContentRef} className="absolute inset-0 flex items-center justify-center z-10 pointer-events-none transition-transform duration-100 ease-out">
          <HeroContent />
        </div>
      </div>
    </div>
  );
};

export { HeroSection }
