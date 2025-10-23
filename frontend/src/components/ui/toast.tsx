import * as React from 'react';

import { cn } from '@/lib/utils';

const Toast = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    variant?: 'default' | 'destructive';
  }
>(({ className, variant = 'default', ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        'pointer-events-auto relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-md border p-6 pr-8 shadow-lg transition-all',
        variant === 'destructive'
          ? 'border-red-200 bg-red-50 text-red-900'
          : 'border-gray-200 bg-white',
        className
      )}
      {...props}
    />
  );
});
Toast.displayName = 'Toast';

const ToastTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => {
  return (
    <h3
      ref={ref}
      className={cn('text-sm font-semibold', className)}
      {...props}
    />
  );
});
ToastTitle.displayName = 'ToastTitle';

const ToastDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => {
  return (
    <p ref={ref} className={cn('text-sm opacity-90', className)} {...props} />
  );
});
ToastDescription.displayName = 'ToastDescription';

export { Toast, ToastDescription, ToastTitle };
