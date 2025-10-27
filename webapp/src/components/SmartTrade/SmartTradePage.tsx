import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { CandleChart } from '../Chart/CandleChart';
import { Skeleton } from '../ui/skeleton';
import { useState } from 'react';

export const SmartTradePage = (): JSX.Element => {
  const [showChart, setShowChart] = useState(true);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-white">Smart Trade</h2>
          <p className="text-sm text-slate-400">Monitor price, manage orders and keep track of risk in real time.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline">Start WebSocket</Button>
          <Button onClick={() => setShowChart((prev) => !prev)}>Toggle chart</Button>
        </div>
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Candles</CardTitle>
            <CardDescription>5 minute BTCUSDT candles from local database</CardDescription>
          </CardHeader>
          <CardContent>{showChart ? <CandleChart /> : <Skeleton className="h-96 w-full" />}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Order Ticket</CardTitle>
            <CardDescription>Send market, limit or bracket orders.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 text-sm text-slate-300">
              <p>Order form coming soon.</p>
              <Button className="w-full">New Market Order</Button>
              <Button variant="outline" className="w-full">
                Configure Bracket
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Positions</CardTitle>
            <CardDescription>Open positions synced from Bitget / paper broker.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-2xl border border-border/60 bg-slate-900/40 p-6 text-sm text-slate-400">
              No open positions.
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Alerts</CardTitle>
            <CardDescription>Set price or indicator-based alerts.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm text-slate-300">
              <p>You can create alerts and they will sync every 2 seconds.</p>
              <Button variant="outline" className="w-full">
                New Alert
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
