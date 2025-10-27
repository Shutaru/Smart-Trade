import * as React from 'react';
import { cn } from '../../lib/cn';

const Table = ({ className, ...props }: React.HTMLAttributes<HTMLTableElement>) => (
  <div className="w-full overflow-x-auto rounded-2xl border border-border bg-surface">
    <table className={cn('w-full caption-bottom text-sm text-slate-200', className)} {...props} />
  </div>
);

const TableHeader = ({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) => (
  <thead className={cn('bg-surface/80 text-xs uppercase tracking-wide text-slate-400', className)} {...props} />
);

const TableBody = ({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) => (
  <tbody className={cn('divide-y divide-border/60', className)} {...props} />
);

const TableRow = ({ className, ...props }: React.HTMLAttributes<HTMLTableRowElement>) => (
  <tr className={cn('hover:bg-slate-800/40 transition-colors', className)} {...props} />
);

const TableHead = ({ className, ...props }: React.ThHTMLAttributes<HTMLTableCellElement>) => (
  <th className={cn('px-4 py-3 text-left font-medium', className)} {...props} />
);

const TableCell = ({ className, ...props }: React.TdHTMLAttributes<HTMLTableCellElement>) => (
  <td className={cn('px-4 py-3', className)} {...props} />
);

export { Table, TableHeader, TableBody, TableRow, TableHead, TableCell };
