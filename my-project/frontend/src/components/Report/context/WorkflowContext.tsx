/**
 * ワークフロー管理用Reactコンテキスト（useReducer + useMemoベース）
 * 
 * 🚀 根本的なパフォーマンス最適化:
 * - useReducerによる予測可能な状態管理
 * - useMemoによるアクション関数とコンテキスト値の安定化
 * - 無限レンダリングループの完全回避
 * 
 * 🔧 保守性向上:
 * - ActionTypeによる型安全な状態更新
 * - 中央集権的な状態管理パターン
 * - テスタブルなReducer関数
 * 
 * 💡 設計原則:
 * - Single Source of Truth
 * - Immutable State Updates
 * - Predictable State Transitions
 */
import React, { createContext, useContext, useReducer, useMemo } from 'react';

// バックエンドデータの型定義
export type BackendData = Record<string, unknown> | null;

// ユーザー入力データの型定義
export type UserInputData = Record<string, unknown>;

// ワークフロー状態の型定義
export interface WorkflowState {
    currentStep: number;
    backendData: BackendData;
    userInputData: UserInputData;
    loading: boolean;
    error: string | null;
}

// アクションタイプの定義
export type WorkflowAction = 
    | { type: 'SET_CURRENT_STEP'; payload: number }
    | { type: 'SET_BACKEND_DATA'; payload: BackendData }
    | { type: 'SET_USER_INPUT_DATA'; payload: UserInputData }
    | { type: 'UPDATE_USER_INPUT_DATA'; payload: { key: string; value: unknown } }
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'SET_ERROR'; payload: string | null }
    | { type: 'NEXT_STEP'; payload: number } // maxSteps
    | { type: 'PREV_STEP' }
    | { type: 'RESET' };

// アクション作成関数の型定義
export interface WorkflowActions {
    setCurrentStep: (step: number) => void;
    setBackendData: (data: BackendData) => void;
    setUserInputData: (data: UserInputData) => void;
    updateUserInputData: (key: string, value: unknown) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    nextStep: () => void;
    prevStep: () => void;
    reset: () => void;
}

// コンテキストの型定義
export interface WorkflowContextType {
    state: WorkflowState;
    actions: WorkflowActions;
}

// Providerのプロパティ定義
interface WorkflowProviderProps {
    children: React.ReactNode;
    maxSteps?: number;
}

// 初期状態
const initialState: WorkflowState = {
    currentStep: 0,
    backendData: null,
    userInputData: {},
    loading: false,
    error: null,
};

// Reducer関数（予測可能な状態管理）
const workflowReducer = (state: WorkflowState, action: WorkflowAction): WorkflowState => {
    switch (action.type) {
        case 'SET_CURRENT_STEP':
            return { ...state, currentStep: action.payload };
        
        case 'SET_BACKEND_DATA':
            return { ...state, backendData: action.payload };
        
        case 'SET_USER_INPUT_DATA':
            return { ...state, userInputData: action.payload };
        
        case 'UPDATE_USER_INPUT_DATA':
            return {
                ...state,
                userInputData: { 
                    ...state.userInputData, 
                    [action.payload.key]: action.payload.value 
                }
            };
        
        case 'SET_LOADING':
            return { ...state, loading: action.payload };
        
        case 'SET_ERROR':
            return { ...state, error: action.payload };
        
        case 'NEXT_STEP':
            return {
                ...state,
                currentStep: Math.min(state.currentStep + 1, action.payload - 1)
            };
        
        case 'PREV_STEP':
            return {
                ...state,
                currentStep: Math.max(state.currentStep - 1, 0)
            };
        
        case 'RESET':
            return initialState;
        
        default:
            return state;
    }
};

// コンテキスト作成
const WorkflowContext = createContext<WorkflowContextType | null>(null);

// プロバイダーコンポーネント（useReducer + useMemoベース）
export const WorkflowProvider: React.FC<WorkflowProviderProps> = ({ 
    children, 
    maxSteps = 3 
}) => {
    const [state, dispatch] = useReducer(workflowReducer, initialState);

    // アクション作成関数をuseMemoで安定化
    const actions = useMemo<WorkflowActions>(() => ({
        setCurrentStep: (step: number) => {
            const clampedStep = Math.max(0, Math.min(maxSteps - 1, step));
            dispatch({ type: 'SET_CURRENT_STEP', payload: clampedStep });
        },

        setBackendData: (data: BackendData) => {
            dispatch({ type: 'SET_BACKEND_DATA', payload: data });
        },

        setUserInputData: (data: UserInputData) => {
            dispatch({ type: 'SET_USER_INPUT_DATA', payload: data });
        },

        updateUserInputData: (key: string, value: unknown) => {
            dispatch({ type: 'UPDATE_USER_INPUT_DATA', payload: { key, value } });
        },

        setLoading: (loading: boolean) => {
            dispatch({ type: 'SET_LOADING', payload: loading });
        },

        setError: (error: string | null) => {
            dispatch({ type: 'SET_ERROR', payload: error });
        },

        nextStep: () => {
            dispatch({ type: 'NEXT_STEP', payload: maxSteps });
        },

        prevStep: () => {
            dispatch({ type: 'PREV_STEP' });
        },

        reset: () => {
            dispatch({ type: 'RESET' });
        },
    }), [maxSteps]);

    // コンテキスト値をuseMemoで安定化（これが最も重要）
    const contextValue = useMemo<WorkflowContextType>(() => ({
        state,
        actions,
    }), [state, actions]);

    return (
        <WorkflowContext.Provider value={contextValue}>
            {children}
        </WorkflowContext.Provider>
    );
};

// カスタムフック
export const useWorkflow = (): WorkflowContextType => {
    const context = useContext(WorkflowContext);
    if (!context) {
        throw new Error('useWorkflow must be used within a WorkflowProvider');
    }
    return context;
};

export default WorkflowContext;
