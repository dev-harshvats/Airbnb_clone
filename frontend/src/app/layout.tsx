import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";

import { Providers } from "@/components/auth/Providers";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { MobileTabBar } from "@/components/layout/MobileTabBar";
import "./globals.css";

// A free lookalike for Airbnb's proprietary typeface (SIL Open Font License).
const figtree = localFont({
  src: "../../public/fonts/Figtree-Variable.ttf",
  variable: "--font-figtree",
  weight: "300 900",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Airbnb | Holiday rentals, cabins, beach houses & more",
  description:
    "Find holiday rentals, cabins, beach houses, unique homes and experiences across India on Airbnb.",
};

export const viewport: Viewport = {
  themeColor: "#ff385c",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en-IN" className={figtree.variable}>
      <body className="min-h-screen antialiased">
        <Header />
        {children}
        <Footer />
        <MobileTabBar />
        <Providers />
      </body>
    </html>
  );
}
