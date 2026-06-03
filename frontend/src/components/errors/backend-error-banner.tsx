import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface BackendErrorBannerProps {
  onRetry: () => void;
}

export function BackendErrorBanner({ onRetry }: BackendErrorBannerProps) {
  return (
    <Alert variant="destructive" className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-col gap-1">
        <AlertTitle>Unable to reach the server</AlertTitle>
        <AlertDescription>
          Check your connection and ensure the backend is running, then try again.
        </AlertDescription>
      </div>
      <Button type="button" variant="outline" onClick={onRetry}>
        Retry
      </Button>
    </Alert>
  );
}
