import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";
import { ElectronProvider } from "@/components/ElectronProvider";
import { ApiUsageBanner } from "@/components/ApiUsageIndicator";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Real Estate Deal Platform",
  description: "Source, analyze, and rank real estate investment opportunities",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ElectronProvider>
          <div className="min-h-screen bg-gray-50 flex flex-col">
            <Navigation />
            <ApiUsageBanner />
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
              {children}
            </main>
            <Footer />
          </div>
        </ElectronProvider>
      </body>
    </html>
  );
}
