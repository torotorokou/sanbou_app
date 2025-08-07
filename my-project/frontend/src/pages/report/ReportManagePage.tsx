import React, { useState } from 'react';
import ReportManagePageLayout from '../../components/Report/common/ReportManagePageLayout';
import { Select, Space, Steps } from 'antd';
import { useReportManager } from '../../hooks/useReportManager';
import { REPORT_KEYS, reportApiUrlMap } from '../../constants/reportConfig/managementReportConfig.tsx';
import type { ReportKey, CsvConfigEntry } from '../../constants/reportConfig/managementReportConfig.tsx';

/**
 * 管理帳簿ページ - 統一レイアウト + プルダウン + API連携
 * 
 * 🔄 修正内容：
 * - プルダウンUI復活（Select）
 * - バックエンドAPI連携復活（FormData → ZIP）
 * - 統一レイアウト（ReportManagePageLayout）
 * - 適切なエンドポイント（/api/reports/generate）
 */

const ReportManagePage: React.FC = () => {
    // 管理帳簿用のレポートマネージャー
    const reportManager = useReportManager('factory_report');

    // CSVファイル管理
    const [csvFiles, setCsvFiles] = useState<Record<string, File | null>>({});

    // 現在の設定を取得
    const currentConfig = reportManager.selectedConfig;

    // CSVアップロード用のファイル情報を作成
    const createUploadFiles = () => {
        return currentConfig.csvConfigs.map((csvConfig: CsvConfigEntry) => ({
            label: csvConfig.config.label,
            file: csvFiles[csvConfig.config.label] || null,
            onChange: (file: File | null) => {
                setCsvFiles(prev => ({
                    ...prev,
                    [csvConfig.config.label]: file,
                }));
            },
            required: csvConfig.required,
            validationResult: reportManager.getValidationResult(csvConfig.config.label),
            onRemove: () => {
                setCsvFiles(prev => ({
                    ...prev,
                    [csvConfig.config.label]: null,
                }));
            },
        }));
    };

    const makeUploadProps = (label: string, setter: (file: File) => void) => ({
        name: 'file',
        multiple: false,
        beforeUpload: (file: File) => {
            setter(file);
            return false; // ファイルアップロードを停止
        },
        onRemove: () => {
            setCsvFiles(prev => ({
                ...prev,
                [label]: null,
            }));
        },
    });

    // バックエンドAPI連携での帳簿生成
    const handleGenerate = async () => {
        try {
            reportManager.setCurrentStep(2);

            // FormDataを作成してCSVファイルを含める
            const formData = new FormData();
            formData.append('reportKey', reportManager.selectedReport);
            formData.append('reportType', currentConfig.type);

            // CSVファイルを追加
            Object.entries(csvFiles).forEach(([label, file]) => {
                if (file) {
                    formData.append('csvFiles', file, `${label}.csv`);
                }
            });

            // バックエンドAPIへリクエスト（設定ファイルからエンドポイントを取得）
            const apiUrl = reportApiUrlMap[reportManager.selectedReport];
            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            // ZIP形式のレスポンスを処理
            const blob = await response.blob();
            const zipUrl = URL.createObjectURL(blob);

            // 結果を設定
            reportManager.setCurrentStep(3);

            // ZIP URLを保存（ダウンロード用）
            sessionStorage.setItem('lastGeneratedZip', zipUrl);

        } catch (error) {
            console.error('Report generation error:', error);
            reportManager.setCurrentStep(1);
        }
    };

    // 生成準備完了チェック
    const readyToCreate = currentConfig.csvConfigs
        .filter((config: CsvConfigEntry) => config.required)
        .every((config: CsvConfigEntry) => csvFiles[config.config.label]);

    // ヘッダー部分：プルダウン + ステッパー
    const header = (
        <div style={{ marginBottom: 16 }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 12
            }}>
                {/* 左側：タイトル + プルダウン */}
                <Space size="large" align="center">
                    <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>
                        管理帳簿システム 📊
                    </h2>
                    <Select
                        value={reportManager.selectedReport}
                        onChange={(value: ReportKey) => reportManager.changeReport(value)}
                        style={{ width: 200 }}
                        options={Object.entries(REPORT_KEYS).map(([key, config]) => ({
                            value: key,
                            label: config.label,
                        }))}
                    />
                </Space>

                {/* 右側：ステッパー */}
                <div style={{ minWidth: 300 }}>
                    <Steps
                        current={reportManager.currentStep - 1}
                        size="small"
                        items={[
                            { title: 'CSV準備' },
                            { title: '帳簿生成' },
                            { title: '結果確認' },
                        ]}
                    />
                </div>
            </div>
        </div>
    );

    return (
        <ReportManagePageLayout
            header={header}
            uploadFiles={createUploadFiles()}
            makeUploadProps={makeUploadProps}
            onGenerate={handleGenerate}
            onDownloadExcel={() => {
                // ZIP形式でのダウンロード
                const zipUrl = sessionStorage.getItem('lastGeneratedZip');
                if (zipUrl) {
                    const a = document.createElement('a');
                    a.href = zipUrl;
                    a.download = `管理帳簿_${reportManager.selectedReport}_${Date.now()}.zip`;
                    a.click();
                }
            }}
            onPrintPdf={() => {
                // PDF印刷処理（実装が必要）
                console.log('PDF print');
            }}
            finalized={reportManager.currentStep === 3}
            readyToCreate={readyToCreate}
            pdfUrl={null} // 実装が必要
            excelUrl={sessionStorage.getItem('lastGeneratedZip')}
            excelReady={!!sessionStorage.getItem('lastGeneratedZip')}
            pdfReady={false} // 実装が必要
            sampleImageUrl={currentConfig.previewImage}
        >
            <div style={{
                padding: 20,
                textAlign: 'center',
                backgroundColor: '#f6f6f6',
                borderRadius: 8
            }}>
                <h3>管理帳簿プレビュー</h3>
                <p>選択された帳簿: {REPORT_KEYS[reportManager.selectedReport].label}</p>
                <p>ステップ: {reportManager.currentStep}/3</p>
                {!!sessionStorage.getItem('lastGeneratedZip') && (
                    <p style={{ color: '#52c41a', fontWeight: 600 }}>
                        ✅ ZIP形式のレポートが生成されました
                    </p>
                )}
            </div>
        </ReportManagePageLayout>
    );
};

export default ReportManagePage;
