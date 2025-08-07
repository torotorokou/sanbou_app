import type { ReportBaseProps } from './reportBase';

// インタラクティブワークフローの基本インターフェース
export interface InteractiveWorkflowProps extends ReportBaseProps {
    getValidationResult?: (label: string) => 'valid' | 'invalid' | 'unknown';
    currentStep: number;
    stepConfig?: unknown;
}

// ワークフローステップの定義
export interface WorkflowStep {
    label: string;
    description: string;
    isSkippable?: boolean;
    requiresUserInput?: boolean;
}

// ワークフローコンポーネントの基本インターフェース
export interface InteractiveWorkflowComponent {
    steps: WorkflowStep[];
    currentStep: number;
    onStepChange: (step: number) => void;
    onComplete: () => void;
    onError: (error: string) => void;
}

// API レスポンスの共通型
export type ApiResponse<T> = {
    status: 'success' | 'error';
    code: string;
    detail: string;
    result: T | null;
    hint?: string;
};

// 汎用的なワークフローステート
export interface WorkflowState<T = unknown> {
    currentStep: number;
    data: T | null;
    loading: boolean;
    error: string | null;
    completed: boolean;
}

// ワークフローアクション
export type WorkflowAction<T = unknown> =
    | { type: 'START' }
    | { type: 'SET_STEP'; step: number }
    | { type: 'SET_DATA'; data: T }
    | { type: 'SET_LOADING'; loading: boolean }
    | { type: 'SET_ERROR'; error: string | null }
    | { type: 'COMPLETE' }
    | { type: 'RESET' };
