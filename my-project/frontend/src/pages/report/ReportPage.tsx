// src/pages/report/ReportPage.tsx

import React, { useState, useEffect } from 'react';
import ReportBase from '@/components/Report/ReportBase';
import ReportHeader from '@/components/Report/common/ReportHeader';
import {
    reportConfigMap,
    pdfPreviewMap,
} from '@/constants/reportConfig/managementReportConfig';
import type {
    ReportKey,
    CsvConfigEntry,
} from '@/constants/reportConfig/managementReportConfig';

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

    const handleReportChange = (val: string) => {
        setSelected(val as ReportKey);
        setPreviewUrl(null);
        setFinalized(false);
        setModalOpen(false);
        setLoading(false);
    };

    const handleCsvUpload = (label: string, file: File | null) => {
        setCsvFiles((prev) => ({
            ...prev,
            [label]: file,
        }));
    };

    const selectedConfig = reportConfigMap[selected];
    const currentCsvFiles: CsvFiles = {};
    selectedConfig.csvConfigs.forEach((entry) => {
        currentCsvFiles[entry.config.label] =
            csvFiles[entry.config.label] ?? null;
    });

    // ✅ 必須CSVがすべてアップロードされているかを判定
    const areRequiredCSVsUploaded = (): boolean => {
        return selectedConfig.csvConfigs
            .filter((entry) => entry.required)
            .every((entry) => csvFiles[entry.config.label]);
    };

    useEffect(() => {
        if (!areRequiredCSVsUploaded()) {
            setCurrentStep(0);
            return;
        }
        if (!finalized) {
            setCurrentStep(1);
            return;
        }
        if (finalized && previewUrl) {
            setCurrentStep(2);
            return;
        }
        setCurrentStep(0);
    }, [selected, csvFiles, finalized, previewUrl, selectedConfig.csvConfigs]);

    // propsグループ化
    const stepProps = {
        steps: selectedConfig.steps,
        currentStep,
        setCurrentStep,
    };
    const fileProps = {
        csvConfigs: selectedConfig.csvConfigs,
        files: currentCsvFiles,
        onUploadFile: handleCsvUpload,
    };
    const previewProps = {
        previewUrl,
        setPreviewUrl,
    };
    const modalProps = {
        modalOpen,
        setModalOpen,
    };
    const finalizedProps = {
        finalized,
        setFinalized,
    };
    const loadingProps = {
        loading,
        setLoading,
    };

    return (
        <>
            <ReportHeader
                reportKey={selected}
                onChangeReportKey={handleReportChange}
                currentStep={currentStep}
            />
            <ReportBase
                step={stepProps}
                file={fileProps}
                preview={previewProps}
                modal={modalProps}
                finalized={finalizedProps}
                loading={loadingProps}
                generatePdf={selectedConfig.generatePdf}
                reportKey={selected} // ← これを追加！！
            />
        </>
    );
};

export default ReportPage;
