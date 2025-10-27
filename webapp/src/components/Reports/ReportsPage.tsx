import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';

const reports = [
  { name: 'Backtest 2024-04-11', type: 'Backtest', path: '/data/backtests/run-20240411/report.html' },
  { name: 'Optuna v12', type: 'Optuna', path: '/data/ml_optuna/optuna-v12/report.html' },
];

export const ReportsPage = (): JSX.Element => (
  <div className="space-y-6">
    <Card>
      <CardHeader>
        <CardTitle>Reports</CardTitle>
        <CardDescription>Explore generated analytics directly inside the terminal.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reports.map((report) => (
              <TableRow key={report.name}>
                <TableCell>{report.name}</TableCell>
                <TableCell>{report.type}</TableCell>
                <TableCell>
                  <Button size="sm" variant="outline" asChild>
                    <a href={report.path} target="_blank" rel="noreferrer">
                      Open
                    </a>
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </div>
);
