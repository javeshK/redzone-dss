import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('RedZone DSS render error:', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="page error-panel">
          <h2>Dashboard error</h2>
          <p>{this.state.error.message}</p>
          <button
            type="button"
            className="btn-primary"
            onClick={() => this.setState({ error: null })}
          >
            Dismiss
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
