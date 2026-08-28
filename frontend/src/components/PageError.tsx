interface PageErrorProps {
  message: string;
  onRetry?: () => void;
}

export default function PageError({ message, onRetry }: PageErrorProps) {
  return (
    <div className="page error-panel">
      <h2>Something went wrong</h2>
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="btn-primary" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
