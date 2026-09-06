import { t } from '../i18n';

export type WorkflowStep = 'map' | 'habitation' | 'planner';

interface WorkflowStepsProps {
  current: WorkflowStep;
  habitationName?: string;
}

const STEPS: { id: WorkflowStep; labelKey: string }[] = [
  { id: 'map', labelKey: 'workflow.map' },
  { id: 'habitation', labelKey: 'workflow.habitation' },
  { id: 'planner', labelKey: 'workflow.planner' },
];

export default function WorkflowSteps({ current, habitationName }: WorkflowStepsProps) {
  const currentIdx = STEPS.findIndex((s) => s.id === current);

  return (
    <nav className="workflow-steps" aria-label={t('workflow.aria')}>
      {STEPS.map((step, idx) => {
        const done = idx < currentIdx;
        const active = idx === currentIdx;
        return (
          <div
            key={step.id}
            className={`workflow-step${done ? ' done' : ''}${active ? ' active' : ''}`}
          >
            <span className="workflow-num">{idx + 1}</span>
            <span className="workflow-label">{t(step.labelKey)}</span>
          </div>
        );
      })}
      {habitationName && (
        <span className="workflow-context">
          {t('workflow.for')} <strong>{habitationName}</strong>
        </span>
      )}
    </nav>
  );
}
