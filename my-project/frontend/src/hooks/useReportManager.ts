import { useState, useEffect, useCallback } from 'react';
import { reportConfigMap } from '../constants/reportConfig/managementReportConfig.tsx';
import type { ReportKey } from '../constants/reportConfig/managementReportConfig.tsx';

// CSVファイルの型定義
type CsvFiles = { [csvLabel: string]: File | null };

/**
 * レポート管理用のカスタムフック
 *
 * 🎯 目的：
 * - ReportPageの複雑なロジックを分離し、状態管理を簡潔にする
 * - レポートタイプ、CSVファイル、ステップ管理を一元化する
 * - 再利用可能で保守しやすいコードを提供する
 *
 * 🔧 主な機能：
 * - レポートタイプの切り替え
 * - CSVファイルのアップロード管理
 * - ステップの自動遷移
 * - プレビュー・モーダル状態管理
 *
 * @param initialReportKey 初期レポートタイプ（デフォルト: 'factory_report'）
 * @returns レポート管理に必要な状態とアクション
 */
export const useReportManager = (
    initialReportKey: ReportKey = 'factory_report'
) => {
    // 基本状態
    const [selectedReport, setSelectedReport] =
        useState<ReportKey>(initialReportKey);
    const [csvFiles, setCsvFiles] = useState<CsvFiles>({});
    const [currentStep, setCurrentStep] = useState(0);

    // プレビュー・モーダル関連状態
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [isFinalized, setIsFinalized] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    // 現在選択されているレポートの設定を取得
    const selectedConfig = reportConfigMap[selectedReport];

    /**
     * レポートタイプを変更する
     */
    const changeReport = useCallback((reportKey: string) => {
        setSelectedReport(reportKey as ReportKey);
        // 状態をリセット
        setPreviewUrl(null);
        setIsFinalized(false);
        setIsModalOpen(false);
        setIsLoading(false);
    }, []);

    /**
     * CSVファイルをアップロードする
     */
    const uploadCsvFile = useCallback((label: string, file: File | null) => {
        setCsvFiles((prev) => ({
            ...prev,
            [label]: file,
        }));
    }, []);

    /**
     * 現在のレポートに必要なCSVファイルを取得
     */
    const getCurrentCsvFiles = useCallback((): CsvFiles => {
        const result: CsvFiles = {};
        selectedConfig.csvConfigs.forEach((entry) => {
            result[entry.config.label] = csvFiles[entry.config.label] ?? null;
        });
        return result;
    }, [selectedConfig.csvConfigs, csvFiles]);

    /**
     * 必須CSVがすべてアップロードされているかチェック
     */
    const areRequiredCsvsUploaded = useCallback((): boolean => {
        return selectedConfig.csvConfigs
            .filter((entry) => entry.required)
            .every((entry) => csvFiles[entry.config.label]);
    }, [selectedConfig.csvConfigs, csvFiles]);

    /**
     * ステップを自動的に更新する
     */
    useEffect(() => {
        if (!areRequiredCsvsUploaded()) {
            setCurrentStep(0);
            return;
        }

        if (!isFinalized) {
            setCurrentStep(1);
            return;
        }

        if (isFinalized && previewUrl) {
            setCurrentStep(2);
            return;
        }

        setCurrentStep(0);
    }, [
        selectedReport,
        csvFiles,
        isFinalized,
        previewUrl,
        areRequiredCsvsUploaded,
    ]);

    return {
        // 状態
        selectedReport,
        csvFiles: getCurrentCsvFiles(),
        currentStep,
        previewUrl,
        isFinalized,
        isModalOpen,
        isLoading,
        selectedConfig,

        // アクション
        changeReport,
        uploadCsvFile,
        setCurrentStep,
        setPreviewUrl,
        setIsFinalized,
        setIsModalOpen,
        setIsLoading,

        // 計算されたプロパティ
        areRequiredCsvsUploaded: areRequiredCsvsUploaded(),

        // ヘルパー関数：ReportBaseコンポーネント用のpropsを生成
        getReportBaseProps: () => ({
            step: {
                steps: selectedConfig.steps,
                currentStep,
                setCurrentStep,
            },
            file: {
                csvConfigs: selectedConfig.csvConfigs,
                files: getCurrentCsvFiles(),
                onUploadFile: uploadCsvFile,
            },
            preview: {
                previewUrl,
                setPreviewUrl,
            },
            modal: {
                modalOpen: isModalOpen,
                setModalOpen: setIsModalOpen,
            },
            finalized: {
                finalized: isFinalized,
                setFinalized: setIsFinalized,
            },
            loading: {
                loading: isLoading,
                setLoading: setIsLoading,
            },
            generatePdf: selectedConfig.generatePdf,
            reportKey: selectedReport,
        }),
    };
};
