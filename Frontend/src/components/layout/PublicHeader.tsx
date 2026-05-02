import { Logo } from "./Logo";

export const PublicHeader = () => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/5 bg-black/80 backdrop-blur-md">
      <div className="container flex h-16 items-center">
        <Logo className="text-white" />
      </div>
    </header>
  );
};