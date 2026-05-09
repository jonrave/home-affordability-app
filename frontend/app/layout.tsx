import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "Home Affordability",
  description: "Household home affordability model"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
