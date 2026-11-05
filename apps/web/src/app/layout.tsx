import type { Metadata } from 'next';
import localFont from 'next/font/local';
import './globals.css';
import './workspace.css';
import { ToastProvider } from '@/context/ToastContext';
import { ResumeProvider } from '@/context/ResumeContext';
import { AuthProvider } from '@/context/AuthContext';

const plexSans = localFont({
  src: './fonts/GeistVF.woff',
  variable: '--font-plex-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'UniTalent AI — Tìm việc bằng năng lực thật',
  description: 'Tải CV một lần, xem mức độ phù hợp với nhiều công việc và theo dõi đơn ứng tuyển. Nhà tuyển dụng xem hồ sơ, kỹ năng và dự án trong cùng một nơi.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className={plexSans.variable}>
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <ToastProvider>
          <AuthProvider><ResumeProvider>{children}</ResumeProvider></AuthProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
