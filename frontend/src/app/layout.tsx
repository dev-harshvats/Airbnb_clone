import type { Metadata, Viewport } from "next";
import "./globals.css";

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
    <html lang="en-IN">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
