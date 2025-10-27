import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';

export const BotsPage = (): JSX.Element => (
  <div className="space-y-6">
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-2xl font-semibold text-white">Automation</h2>
        <p className="text-sm text-slate-400">Configure algorithmic agents to auto-execute trade ideas.</p>
      </div>
      <Button>Create Bot</Button>
    </div>
    <Card>
      <CardHeader>
        <CardTitle>Coming soon</CardTitle>
        <CardDescription>We are preparing a full automation builder with guard rails.</CardDescription>
      </CardHeader>
      <CardContent className="text-sm text-slate-300">
        <p>Define entry triggers, risk profiles and exit automation for your strategies in minutes.</p>
      </CardContent>
    </Card>
  </div>
);
