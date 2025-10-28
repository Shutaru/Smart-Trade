import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface ExitRulesEditorProps {
  value: { long: any[]; short: any[] };
  onChange: (value: any) => void;
}

export function ExitRulesEditor({ value, onChange }: ExitRulesEditorProps) {
  // Suppress unused warnings - these will be used when we implement the actual logic
  void value;
  void onChange;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Exit Rules</CardTitle>
        <CardDescription>Define exit strategies (TP/SL, trailing stops, etc.)</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Exit Rule Type</Label>
            <Select defaultValue="tp_sl_fixed">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="tp_sl_fixed">Fixed TP/SL</SelectItem>
                <SelectItem value="atr_trailing">ATR Trailing</SelectItem>
                <SelectItem value="chandelier">Chandelier</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Take Profit %</Label>
              <Input type="number" placeholder="2.0" defaultValue="2.0" />
            </div>
            <div className="space-y-2">
              <Label>Stop Loss %</Label>
              <Input type="number" placeholder="1.0" defaultValue="1.0" />
            </div>
          </div>

          <p className="text-xs text-muted-foreground">
            Exit rules apply to both long and short positions
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
