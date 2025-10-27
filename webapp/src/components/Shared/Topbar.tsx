import React from 'react';
import { Badge } from "@/components/ui/badge";
import { Clock, Briefcase, DollarSign, Zap } from 'lucide-react';

const Topbar: React.FC = () => {
  return (
    <header className="flex items-center justify-between p-4 bg-surface border-b border-border">
      <div className="flex items-center space-x-4">
        <Badge variant="outline">Paper Mode</Badge>
        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <Briefcase size={16} />
          <span>BTC/USD</span>
        </div>
      </div>
      <div className="flex items-center space-x-6 text-sm">
        <div className="flex items-center space-x-2">
          <DollarSign size={16} />
          <span>Balance: $10,000</span>
        </div>
        <div className="flex items-center space-x-2">
            <Zap size={16} />
            <span>Funding: 0.01%</span>
        </div>
        <div className="flex items-center space-x-2 text-muted-foreground">
          <Clock size={16} />
          <span>{new Date().toLocaleTimeString()}</span>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
