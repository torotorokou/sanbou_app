import React, { useState, useEffect } from 'react';
import ReportBase from '@/components/Report/ReportBase';
import ReportHeader from '@/components/Report/common/ReportHeader';
import { factoryConfig, attendanceConfig } from './reportConfigs';

const configMap = {
    factory: factoryConfig,
    attendance: attendanceConfig,
    // 他帳票もここに追加可能
};

type ReportKey = keyof typeof configMap;

// CSVはラベルごとにグローバルで管理
type CsvFiles = { [csvLabel: string]: File | null };

const ReportPage: React.FC = () => {
    const [selected, setSelected] = useState<ReportKey>('factory');
    const [currentStep, setCurrentStep] = useState(0);
    const [csvFiles, setCsvFiles] = useState<CsvFiles>({});
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [finalized, setFinalized] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [loading, setLoading] = useState(false);

    // 帳票切り替え時はCSV以外リセット
    const handleReportChange = (val: string) => {
        setSelected(val as ReportKey);
        setPreviewUrl(null);
        setFinalized(false);
        setModalOpen(false);
        setLoading(false);
        // CSVは保持したまま
    };

    // CSVアップロード処理
    const handleCsvUpload = (label: string, file: File | null) => {
        setCsvFiles((prev) => ({
            ...prev,
            [label]: file,
        }));
    };

    // 現在の帳票で必要なラベルだけを抽出して渡す
    const selectedConfig = configMap[selected];
    const currentCsvFiles: CsvFiles = {};
    selectedConfig.csvConfigs.forEach((cfg) => {
        currentCsvFiles[cfg.label] = csvFiles[cfg.label] ?? null;
    });

    // ★ 状態とcurrentStepを自動連動させる
    useEffect(() => {
        // すべてのCSVが揃っていなければ ステップ0（アップロード待ち）
        const allFilesReady = selectedConfig.csvConfigs.every(
            (cfg) => csvFiles[cfg.label]
        );
        if (!allFilesReady) {
            setCurrentStep(0);
            return;
        }
        // CSV揃い済み、まだ帳票未生成
        if (allFilesReady && !finalized) {
            setCurrentStep(1);
            return;
        }
        // 帳票生成済み・プレビューあり
        if (finalized && previewUrl) {
            setCurrentStep(2);
            return;
        }
        // その他は明示的に何もしない（念のため0）
        setCurrentStep(0);
    }, [selected, csvFiles, finalized, previewUrl, selectedConfig.csvConfigs]);

    return (
        <>
            <ReportHeader
                reportKey={selected}
                onChangeReportKey={handleReportChange}
                currentStep={currentStep}
            />
            <ReportBase
                {...selectedConfig}
                reportKey={selected}
                setCurrentStep={setCurrentStep}
                currentStep={currentStep}
                files={currentCsvFiles}
                onUploadFile={handleCsvUpload}
                previewUrl={previewUrl}
                setPreviewUrl={setPreviewUrl}
                finalized={finalized}
                setFinalized={setFinalized}
                modalOpen={modalOpen}
                setModalOpen={setModalOpen}
                loading={loading}
                setLoading={setLoading}
            />
        </>
    );
};

export default ReportPage;
