import { CopilotKit } from '@copilotkit/react-core';
import { ReactNode } from 'react';
import { Outlet } from 'react-router-dom';

import { ChatPanel } from '@/components/chat/ChatPanel';
import { ChatProvider } from '@/components/chat/ChatProvider';
import { Navbar } from '@/components/navbar';
import { ThemeProvider } from '@/components/theme-provider';
import { Toaster } from '@/components/ui/toaster';
interface RootLayoutProps {
  children?: ReactNode;
}

export function RootLayout({ children }: RootLayoutProps) {
  return (
    <ThemeProvider defaultTheme="auto">
      <ChatProvider>
        <Navbar />
        <CopilotKit
          publicApiKey={import.meta.env.VITE_PUBLIC_COPILOT_API_KEY || ''}
        >
          <main className="page-container">{children || <Outlet />}</main>
        </CopilotKit>
        <ChatPanel />
        <Toaster />
      </ChatProvider>
    </ThemeProvider>
  );
}
