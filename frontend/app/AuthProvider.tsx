'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Spinner } from '@/components/ui/Spinner';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = localStorage.getItem('och_token');
    setIsAuthenticated(!!token);

    if (!token && pathname !== '/login') {
      router.push('/login');
    }
  }, [pathname, router]);

  if (isAuthenticated === null && pathname !== '/login') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Spinner size="lg" />
      </div>
    );
  }

  return <>{children}</>;
}
