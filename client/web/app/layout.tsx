import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pine — Hire software that works for you",
  description:
    "Hire focused AI agents for the work you need done. Connect the accounts you choose, then pay when the work is complete.",
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
