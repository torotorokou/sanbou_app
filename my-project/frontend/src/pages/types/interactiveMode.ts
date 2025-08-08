// /app/src/pages/types/interactiveMode.ts

/**
 * インタラクティブ帳簿生成モード専用の型定義
 * 
 * 🎯 目的：
 * - インタラクティブモードの複雑な状態管理を型安全に行う
 * - ステップベースの処理フローを明確に定義
 * - モーダル表示とユーザーインタラクションを統合管理
 */

import type React from 'react';

// ==============================
// 📊 インタラクティブ処理状態
// ==============================

/**
 * インタラクティブ処理の進行ステップ
 */
export const INTERACTIVE_STEPS = {
    INITIAL: -1,           // 未開始
    PROCESSING: 0,         // データ処理中
    USER_INPUT: 1,         // ユーザー入力待ち
    CALCULATING: 2,        // 最終計算中
    COMPLETED: 3,          // 完了
} as const;

export type InteractiveStep = typeof INTERACTIVE_STEPS[keyof typeof INTERACTIVE_STEPS];

/**
 * セッションデータの型
 */
export interface SessionData {
    [key: string]: string | number | boolean | object | null;
}

/**
 * ユーザー選択データの型
 */
export interface UserSelections {
    [key: string]: string | number | boolean | string[];
}

/**
 * 処理データの型
 */
export interface ProcessData {
    [key: string]: unknown;
}

/**
 * インタラクティブ処理の状態
 */
export interface InteractiveProcessState {
    currentStep: InteractiveStep;
    isLoading: boolean;
    error?: string;
    sessionData?: SessionData;
    userSelections?: UserSelections;
    processData?: ProcessData;
}

// ==============================
// 🔧 インタラクティブコンポーネント設定
// ==============================

/**
 * 入力値の型
 */
export type InputValue = string | number | boolean | string[] | null;

/**
 * インタラクティブコンポーネントのprops
 */
export interface InteractiveComponentProps {
    state: InteractiveProcessState;
    onStateChange: (newState: Partial<InteractiveProcessState>) => void;
    onComplete: (result: InteractiveResult) => void;
    onError: (error: string) => void;
}

/**
 * インタラクティブコンポーネントの設定
 */
export interface InteractiveComponentConfig {
    component: React.ComponentType<InteractiveComponentProps>;
    title: string;
    description: string;
}

// ==============================
// 🎮 ユーザーインタラクション種類
// ==============================

/**
 * インタラクションの種類
 */
export const INTERACTION_TYPES = {
    SELECT: 'select',           // 選択肢から選択
    INPUT: 'input',             // テキスト入力
    SLIDER: 'slider',           // スライダー操作
    CHECKBOX: 'checkbox',       // チェックボックス
    CUSTOM: 'custom',           // カスタムコンポーネント
} as const;

export type InteractionType = typeof INTERACTION_TYPES[keyof typeof INTERACTION_TYPES];

/**
 * ユーザーインタラクション設定
 */
export interface InteractionConfig {
    id: string;
    type: InteractionType;
    label: string;
    required?: boolean;
    options?: Array<{
        value: string | number;
        label: string;
        description?: string;
    }>;
    validation?: (value: InputValue) => boolean | string;
    defaultValue?: InputValue;
}

// ==============================
// 📋 インタラクティブステップ設定
// ==============================

/**
 * インタラクティブステップの設定
 */
export interface InteractiveStepConfig {
    step: InteractiveStep;
    title: string;
    description?: string;
    component?: React.ComponentType<InteractiveComponentProps>;
    interactions?: InteractionConfig[];
    skipCondition?: (state: InteractiveProcessState) => boolean;
    nextAction: (state: InteractiveProcessState) => Promise<Partial<InteractiveProcessState>>;
}

// ==============================
// 🌊 処理フローの型定義
// ==============================

/**
 * インタラクティブ処理フローの設定
 */
export interface InteractiveFlowConfig {
    reportKey: string;
    steps: InteractiveStepConfig[];
    initialState: Partial<InteractiveProcessState>;
    apiEndpoint: string;
}

// ==============================
// 📡 API通信関連の型
// ==============================

/**
 * インタラクティブAPI リクエスト
 */
export interface InteractiveApiRequest {
    action: 'start' | 'update' | 'complete';
    reportKey: string;
    csvFiles?: Record<string, File>;
    sessionData?: SessionData;
    userInput?: UserSelections;
    currentStep?: InteractiveStep;
}

/**
 * インタラクティブAPI レスポンス
 */
export interface InteractiveApiResponse {
    status: 'success' | 'error' | 'pending';
    message?: string;
    data?: ProcessData;
    sessionData?: SessionData;
    nextStep?: InteractiveStep;
    interactions?: InteractionConfig[];
    error?: string;
}

// ==============================
// 🎯 結果データの型
// ==============================

/**
 * インタラクティブ処理の結果
 */
export interface InteractiveResult {
    success: boolean;
    resultType: 'excel' | 'pdf' | 'zip' | 'json';
    downloadUrl?: string;
    fileName?: string;
    previewUrl?: string;
    summaryData?: ProcessData;
    processingLog?: string[];
}
