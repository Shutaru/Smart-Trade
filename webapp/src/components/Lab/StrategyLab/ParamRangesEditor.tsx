import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface ParamRangesEditorProps {
  value: any[];
  onChange: (value: any) => void;
}

export function ParamRangesEditor({ value, onChange }: ParamRangesEditorProps) {
  // Suppress unused warnings
  void value;
  void onChange;
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Parameter Optimization Ranges</CardTitle>
        <CardDescription>
          Define parameter ranges for grid search or optimization (optional)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
   No parameter ranges defined. For single backtest, parameters are taken from indicator configs.
          Add ranges here for grid search or Optuna optimization.
        </p>
      </CardContent>
    </Card>
  );
}
