import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';

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
  // Calculate suggested position size based on starting equity
  const suggestedPositionSize = Math.floor((value.starting_equity || 10000) * 0.1); // 10% of equity
  const maxPositionSize = Math.floor((value.starting_equity || 10000) * 0.25); // 25% max

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
            onChange={(e) => {
              const newEquity = parseFloat(e.target.value);
              onChange({ ...value, starting_equity: newEquity });
            }}
            placeholder="10000"
            min={1000}
            max={10000000}
          />
          <p className="text-xs text-muted-foreground">
            Initial portfolio value in USDT (min: $1,000, max: $10M)
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Leverage</Label>
            <Input
              type="number"
              value={value.leverage}
              onChange={(e) => onChange({ ...value, leverage: parseFloat(e.target.value) })}
              min={1}
              max={125}
            />
          </div>

          <div className="space-y-2">
            <Label>Max Positions</Label>
            <Input
              type="number"
              value={value.max_concurrent_positions}
              onChange={(e) => onChange({ ...value, max_concurrent_positions: parseInt(e.target.value) })}
              min={1}
              max={10}
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
          <div className="flex flex-col gap-1">
            <p className="text-xs text-muted-foreground">
              {value.position_sizing === 'fixed_usd'
                ? 'Fixed USD value per trade'
                : 'Percentage of equity per trade'}
            </p>
            {value.position_sizing === 'fixed_usd' && (
              <div className="flex gap-2 text-xs">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => onChange({ ...value, size_value: suggestedPositionSize })}
                  className="h-6 text-xs"
                >
                  Suggested: ${suggestedPositionSize.toLocaleString()}
                </Button>
                <span className="text-muted-foreground self-center">
                  (10% of equity, max: ${maxPositionSize.toLocaleString()})
                </span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
