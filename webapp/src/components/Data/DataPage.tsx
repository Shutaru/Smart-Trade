import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { useState } from 'react';

const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'];

export const DataPage = (): JSX.Element => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Bitget Pairs</CardTitle>
          <CardDescription>Choose which contract to download and use in the terminal.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
            <SelectTrigger>
              <SelectValue placeholder="Select symbol" />
            </SelectTrigger>
            <SelectContent>
              {symbols.map((symbol) => (
                <SelectItem key={symbol} value={symbol}>
                  {symbol}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="grid gap-3 md:grid-cols-2">
            <Input type="number" placeholder="Days to backfill" />
            <Input placeholder="Database path" />
          </div>
          <div className="flex gap-3">
            <Button className="flex-1">Backfill</Button>
            <Button variant="outline" className="flex-1">
              Apply to config
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
