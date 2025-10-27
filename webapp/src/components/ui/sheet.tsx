import * as SheetPrimitive from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { cn } from '../../lib/cn';

const Sheet = SheetPrimitive.Root;
const SheetTrigger = SheetPrimitive.Trigger;
const SheetClose = SheetPrimitive.Close;

const SheetOverlay = ({ className, ...props }: SheetPrimitive.DialogOverlayProps) => (
  <SheetPrimitive.Overlay
    className={cn('fixed inset-0 z-40 bg-black/60 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0', className)}
    {...props}
  />
);

const SheetContent = ({ className, children, side = 'right', ...props }: SheetPrimitive.DialogContentProps & { side?: 'left' | 'right' }) => (
  <SheetPrimitive.Portal>
    <SheetOverlay />
    <SheetPrimitive.Content
      className={cn(
        'fixed top-0 z-50 h-full w-full max-w-lg border border-border bg-surface shadow-card transition-transform data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right',
        side === 'left' && 'left-0 data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left',
        side === 'right' && 'right-0',
        className,
      )}
      {...props}
    >
      {children}
      <SheetPrimitive.Close className="absolute right-4 top-4 rounded-full p-1 text-slate-400 transition hover:bg-slate-800/60 hover:text-white">
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </SheetPrimitive.Close>
    </SheetPrimitive.Content>
  </SheetPrimitive.Portal>
);

const SheetHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('grid gap-2 px-6 pt-6 text-left', className)} {...props} />
);

const SheetTitle = ({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h2 className={cn('text-lg font-semibold text-white', className)} {...props} />
);

const SheetDescription = ({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
  <p className={cn('text-sm text-slate-400', className)} {...props} />
);

const SheetFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('mt-auto flex flex-col-reverse gap-2 px-6 pb-6 sm:flex-row sm:justify-end', className)} {...props} />
);

export { Sheet, SheetTrigger, SheetClose, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter };
