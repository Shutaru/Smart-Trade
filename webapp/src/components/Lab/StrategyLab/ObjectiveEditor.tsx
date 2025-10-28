import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

interface ObjectiveEditorProps {
  value: { expression: string };
  onChange: (value: any) => void;
}

export function ObjectiveEditor({ value, onChange }: ObjectiveEditorProps) {
  const allowedChars = /^[a-zA-Z0-9_+\-*/()., ]*$/;
  
  const handleChange = (text: string) => {
    if (allowedChars.test(text)) {
      onChange({ expression: text });
    }
  };

  return (
    <Card>
  <CardHeader>
   <CardTitle>Optimization Objective</CardTitle>
        <CardDescription>
          Define the objective function to optimize (e.g., "sharpe", "sharpe - max_dd / 10")
        </CardDescription>
   </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
     <Label>Expression</Label>
<Textarea
value={value.expression}
     onChange={(e) => handleChange(e.target.value)}
       placeholder="sharpe"
       rows={3}
       />
    <p className="text-xs text-muted-foreground">
            Available variables: sharpe, sortino, calmar, total_profit, max_dd, win_rate, profit_factor, avg_trade, trades, exposure
          </p>
   </div>
      </CardContent>
    </Card>
  );
}
