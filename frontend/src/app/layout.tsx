import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";

import { Providers } from "@/components/auth/Providers";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { MobileTabBar } from "@/components/layout/MobileTabBar";
import { THEME_INIT_SCRIPT } from "@/lib/themeScript";
import "./globals.css";

// Airbnb Cereal, in the six weights Airbnb uses. 600 (semibold) has no file of its own and falls to Bold.
const cereal = localFont({
  src: [
    { path: "../../public/fonts/AirbnbCereal-Light.otf", weight: "300", style: "normal" },
    { path: "../../public/fonts/AirbnbCereal-Book.otf", weight: "400", style: "normal" },
    { path: "../../public/fonts/AirbnbCereal-Medium.otf", weight: "500", style: "normal" },
    { path: "../../public/fonts/AirbnbCereal-Bold.otf", weight: "700", style: "normal" },
    { path: "../../public/fonts/AirbnbCereal-ExtraBold.otf", weight: "800", style: "normal" },
    { path: "../../public/fonts/AirbnbCereal-Black.otf", weight: "900", style: "normal" },
  ],
  variable: "--font-cereal",
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
    <html lang="en-IN" className={cereal.variable} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
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
