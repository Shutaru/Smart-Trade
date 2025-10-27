import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';

const jobs = [
  { id: 'backtest-001', status: 'queued', type: 'Backtest', submitted: '2024-04-12 09:00' },
  { id: 'optuna-014', status: 'running', type: 'Optuna', submitted: '2024-04-12 08:10' },
];

export const LabPage = (): JSX.Element => (
  <div className="space-y-6">
    <div className="flex flex-col gap-6 lg:grid lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Backtest</CardTitle>
          <CardDescription>Run a single configuration through the broker simulator.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button className="w-full">Start backtest</Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Grid Search</CardTitle>
          <CardDescription>Explore parameter space with automated reports.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button className="w-full">Launch grid search</Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Walk-Forward</CardTitle>
          <CardDescription>Validate robustness with rolling optimisations.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button className="w-full">Start walk-forward</Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>ML Optuna</CardTitle>
          <CardDescription>Optimise machine learning thresholds and risk.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button className="w-full">Run study</Button>
        </CardContent>
      </Card>
    </div>
    <Card>
      <CardHeader>
        <CardTitle>Job queue</CardTitle>
        <CardDescription>Track asynchronous tasks kicked off from the Strategy Lab.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Submitted</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {jobs.map((job) => (
              <TableRow key={job.id}>
                <TableCell>{job.id}</TableCell>
                <TableCell>
                  <span className="rounded-full bg-indigo-500/10 px-2 py-1 text-xs text-indigo-300">{job.status}</span>
                </TableCell>
                <TableCell>{job.type}</TableCell>
                <TableCell>{job.submitted}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </div>
);
