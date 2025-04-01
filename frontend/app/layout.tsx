import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'VigilBot Dashboard',
  description: 'OSINT Investigation Tool Dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <main className="min-h-screen bg-gray-100">
          {children}
        </main>
      </body>
    </html>
  );
}
