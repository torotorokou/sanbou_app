import React from 'react';
import { Modal, Button, Steps } from 'antd';

// 共通のワークフロー設定型
export interface WorkflowConfig {
    title?: string;
    steps?: Array<{ title: string; content: string }>;
    width?: number;
}

// 共通のワークフロープロパティ
export interface BaseInteractiveWorkflowProps {
    visible?: boolean;
    onClose?: () => void;
    onComplete?: (result: unknown) => void;
    config?: WorkflowConfig;
}

// 共通のワークフロー状態
export interface WorkflowState {
    currentStep: number;
    isLoading: boolean;
    error?: string;
}

// 共通のワークフローアクション
export type WorkflowAction =
    | { type: 'NEXT_STEP' }
    | { type: 'PREV_STEP' }
    | { type: 'RESET' }
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'SET_ERROR'; payload?: string };

// 共通のワークフローReducer
export const workflowReducer = (state: WorkflowState, action: WorkflowAction): WorkflowState => {
    switch (action.type) {
        case 'NEXT_STEP':
            return { ...state, currentStep: state.currentStep + 1, error: undefined };
        case 'PREV_STEP':
            return { ...state, currentStep: Math.max(0, state.currentStep - 1), error: undefined };
        case 'RESET':
            return { currentStep: 0, isLoading: false, error: undefined };
        case 'SET_LOADING':
            return { ...state, isLoading: action.payload };
        case 'SET_ERROR':
            return { ...state, error: action.payload, isLoading: false };
        default:
            return state;
    }
};

// 共通のワークフロー基底コンポーネント
interface BaseWorkflowWrapperProps extends BaseInteractiveWorkflowProps {
    children: React.ReactNode;
    currentStep: number;
    maxSteps: number;
    onNext: () => void;
    onPrev: () => void;
    onReset: () => void;
    canProceed?: boolean;
    isLoading?: boolean;
}

export const BaseWorkflowWrapper: React.FC<BaseWorkflowWrapperProps> = ({
    visible = false,
    onClose,
    config,
    children,
    currentStep,
    maxSteps,
    onNext,
    onPrev,
    onReset,
    canProceed = true,
    isLoading = false
}) => {
    const defaultSteps = Array.from({ length: maxSteps }, (_, i) => ({
        title: `ステップ ${i + 1}`,
        content: `ステップ ${i + 1}`
    }));

    const steps = config?.steps || defaultSteps;

    return (
        <Modal
            title={config?.title || 'ワークフロー'}
            open={visible}
            onCancel={onClose}
            footer={null}
            width={config?.width || 800}
            destroyOnClose
        >
            <Steps current={currentStep} items={steps} className="workflow-steps" />

            <div className="step-content">
                {children}
            </div>

            <div className="workflow-actions">
                {currentStep > 0 && (
                    <Button onClick={onPrev} disabled={isLoading}>
                        前へ
                    </Button>
                )}
                {currentStep > 0 && (
                    <Button onClick={onReset} disabled={isLoading}>
                        最初から
                    </Button>
                )}
                <Button
                    type="primary"
                    onClick={onNext}
                    disabled={!canProceed}
                    loading={isLoading}
                >
                    {currentStep === maxSteps - 1 ? '完了' : '次へ'}
                </Button>
            </div>
        </Modal>
    );
};

// カスタムフック：ワークフロー状態管理
export const useWorkflowState = (initialStep = 0) => {
    const [state, dispatch] = React.useReducer(workflowReducer, {
        currentStep: initialStep,
        isLoading: false,
        error: undefined
    });

    const nextStep = React.useCallback(() => dispatch({ type: 'NEXT_STEP' }), []);
    const prevStep = React.useCallback(() => dispatch({ type: 'PREV_STEP' }), []);
    const reset = React.useCallback(() => dispatch({ type: 'RESET' }), []);
    const setLoading = React.useCallback((loading: boolean) =>
        dispatch({ type: 'SET_LOADING', payload: loading }), []);
    const setError = React.useCallback((error?: string) =>
        dispatch({ type: 'SET_ERROR', payload: error }), []);

    return {
        state,
        nextStep,
        prevStep,
        reset,
        setLoading,
        setError
    };
};
