import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface RiskPanelProps {
  value: {
    starting_equity: number;
    leverage: number;
    position_sizing: string;
    size_value: number;
    max_concurrent_positions: number;
  };
  onChange: (value: any) => void;
}

export function RiskPanel({ value, onChange }: RiskPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Management</CardTitle>
        <CardDescription>Configure portfolio size, position sizing, and risk parameters</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Starting Equity - Portfolio Size */}
        <div className="space-y-2">
          <Label htmlFor="starting-equity">Starting Equity (USDT)</Label>
          <Input
            id="starting-equity"
            type="number"
            value={value.starting_equity || 10000}
            onChange={(e) => onChange({ ...value, starting_equity: parseFloat(e.target.value) })}
            placeholder="10000"
          />
          <p className="text-xs text-muted-foreground">
            Initial portfolio value in USDT (default: $10,000)
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Leverage</Label>
            <Input
              type="number"
              value={value.leverage}
              onChange={(e) => onChange({ ...value, leverage: parseFloat(e.target.value) })}
            />
          </div>

          <div className="space-y-2">
            <Label>Max Positions</Label>
            <Input
              type="number"
              value={value.max_concurrent_positions}
              onChange={(e) => onChange({ ...value, max_concurrent_positions: parseInt(e.target.value) })}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label>Position Sizing</Label>
          <Select value={value.position_sizing} onValueChange={(v) => onChange({ ...value, position_sizing: v })}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="fixed_usd">Fixed USD</SelectItem>
              <SelectItem value="fixed_pct">Fixed % of Capital</SelectItem>
              <SelectItem value="kelly">Kelly Criterion</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Position Size Value</Label>
          <Input
            type="number"
            value={value.size_value}
            onChange={(e) => onChange({ ...value, size_value: parseFloat(e.target.value) })}
            placeholder="1000"
          />
          <p className="text-xs text-muted-foreground">
            {value.position_sizing === 'fixed_usd'
              ? 'Fixed USD value per trade'
              : 'Percentage of equity per trade'}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
