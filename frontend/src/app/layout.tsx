import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Duplicate-Safe Incremental Merge Diagnostics & Repair Platform",
  description: "Data Engineering Capstone Project DEAI-10",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <header className="border-b border-slate-200 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900">
                Duplicate-Safe Merge Platform
              </h1>
              <p className="text-xs text-slate-500 font-mono">
                DEAI-10 | Diagnostics & Deterministic Repair
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-800">
                Phase 1 Scaffolding
              </span>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
