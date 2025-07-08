import React, { useState } from 'react';
import ReportBase from '@/components/Report/ReportBase';
import ReportHeader from '@/components/Report/common/ReportHeader';
import { factoryConfig, attendanceConfig } from './reportConfigs';

const configMap = {
    factory: factoryConfig,
    attendance: attendanceConfig,
    // 他帳票もここに追加可能
};

type ReportKey = keyof typeof configMap;

// ★ CSVはラベルごとにグローバルで管理
type CsvFiles = { [csvLabel: string]: File | null };

const ReportPage: React.FC = () => {
    const [selected, setSelected] = useState<ReportKey>('factory');
    const [currentStep, setCurrentStep] = useState(0);

    // ★ CSVアップロード管理（ラベルごとに保持、帳票関係なし）
    const [csvFiles, setCsvFiles] = useState<CsvFiles>({});

    // 帳票進行・UI制御state
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [finalized, setFinalized] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [loading, setLoading] = useState(false);

    // 帳票切り替え時はCSV以外リセット
    const handleReportChange = (val: string) => {
        setSelected(val as ReportKey);
        setCurrentStep(0);
        setPreviewUrl(null);
        setFinalized(false);
        setModalOpen(false);
        setLoading(false);
    };

    // ★ CSVアップロード処理（ラベルのみで管理）
    const handleCsvUpload = (label: string, file: File | null) => {
        setCsvFiles((prev) => ({
            ...prev,
            [label]: file,
        }));
    };

    // ★ 現在の帳票で必要なラベルだけを抽出して渡す
    const selectedConfig = configMap[selected];
    const currentCsvFiles: CsvFiles = {};
    selectedConfig.csvConfigs.forEach((cfg) => {
        currentCsvFiles[cfg.label] = csvFiles[cfg.label] ?? null;
    });

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
                // 必要なものがあればpropsを追加
            />
        </>
    );
};

export default ReportPage;
