import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
 console.error('Uncaught error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
  if (this.state.hasError) {
    return (
        <div className="flex items-center justify-center min-h-screen bg-background p-4">
          <Card className="max-w-md w-full shadow-soft">
            <CardHeader>
    <div className="flex items-center gap-2">
      <AlertTriangle className="h-6 w-6 text-destructive" />
    <CardTitle>Unexpected Application Error</CardTitle>
      </div>
              <CardDescription>
 Something went wrong. Please try refreshing the page.
              </CardDescription>
    </CardHeader>
            <CardContent>
      {this.state.error && (
         <div className="bg-secondary p-4 rounded-md">
           <p className="text-sm font-mono text-destructive">
                {this.state.error.message}
      </p>
    </div>
              )}
            </CardContent>
    <CardFooter>
 <Button onClick={this.handleReset} className="w-full">
          Refresh Page
        </Button>
            </CardFooter>
    </Card>
 </div>
      );
 }

    return this.props.children;
  }
}

export default ErrorBoundary;
