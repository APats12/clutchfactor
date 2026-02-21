interface ErrorBannerProps {
  message: string
  onRetry?: () => void
}

export function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700">
      <p className="font-medium">Something went wrong</p>
      <p className="mt-1 text-red-600">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 underline hover:no-underline"
        >
          Try again
        </button>
      )}
    </div>
  )
}
