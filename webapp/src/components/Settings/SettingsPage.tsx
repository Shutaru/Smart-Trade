import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useState } from 'react';

const defaultConfig = `{
  "mode": "paper",
  "symbol": "BTCUSDT_UMCBL",
  "risk": {
    "max_notional": 1000,
    "max_leverage": 3
  }
}`;

export const SettingsPage = (): JSX.Element => {
  const [config, setConfig] = useState(defaultConfig);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Config</CardTitle>
          <CardDescription>Review and edit the runtime configuration (JSON preview).</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            className="min-h-[240px] w-full rounded-2xl border border-border bg-slate-950/70 p-4 font-mono text-sm text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            value={config}
            onChange={(event) => setConfig(event.target.value)}
          />
          <div className="flex gap-3">
            <Button className="flex-1">Save changes</Button>
            <Button variant="outline" className="flex-1">
              Snapshot
            </Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Profiles</CardTitle>
          <CardDescription>Import or export parameter presets.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <Input placeholder="Profile name" />
            <Button>Export</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
