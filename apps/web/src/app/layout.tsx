import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "InfraMind AI",
  description: "Intelligent infrastructure automation platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
