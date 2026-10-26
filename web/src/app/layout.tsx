import type { Metadata } from "next";
import { Archivo, IBM_Plex_Mono, Merriweather } from "next/font/google";
import "./globals.css";

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  display: "swap",
});

const merriweather = Merriweather({
  variable: "--font-merriweather",
  subsets: ["latin"],
  display: "swap",
  weight: ["300", "400", "700", "900"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Precedent - Contract Intelligence",
  description:
    "Enterprise contract intelligence agent with retrieval-first architecture",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${archivo.variable} ${merriweather.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-canvas text-ink">
        <script
          dangerouslySetInnerHTML={{
            // Runs before paint so [data-reveal] targets are hidden as early as the
            // server HTML arrives. If JS is unavailable the class is never added and
            // the content stays visible instead of being stuck at opacity 0.
            __html: "document.documentElement.classList.add('js')",
          }}
        />
        {children}
      </body>
    </html>
  );
}
