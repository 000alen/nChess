import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "nChess",
  description: "A browser-based n-dimensional chess prototype.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
