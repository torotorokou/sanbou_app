import React, { useState, useEffect } from 'react';
import ReportManagePageLayout from '../../components/Report/common/ReportManagePageLayout';
import { Select, Space, Steps } from 'antd';
import { useFactoryReportManager } from '../../hooks/useFactoryReportManager';
import { FACTORY_REPORT_KEYS, factoryReportApiUrlMap } from '../../constants/reportConfig/factoryReportConfig.tsx';
import type { FactoryReportKey, FactoryCsvConfigEntry } from '../../constants/reportConfig/factoryReportConfig.tsx';

/**
 * 工場帳簿ページ - ReportManagePageと統一レイアウト
 * 
 * 🔄 統一されたレイアウト構成：
 * - 左上: 帳簿選択プルダウン（Select）
 * - 右上: ステッパー表示（Steps）
 * - CSVアップロード: ReportManagePageLayout内
 * - 帳簿作成ボタン: バックエンドAPI連携  
 * - 結果表示: エクセルダウンロード、PDF印刷、プレビュー（ReportManagePageLayout内）
 * 
 * 📝 修正内容：
 * - プルダウンUI復活
 * - バックエンドAPI連携復活
 * - ZIP形式でのダウンロード対応
 * - 差分は帳簿種類（管理 vs 工場）のみ
 */

const ReportFactory: React.FC = () => {
    // 工場帳簿用のレポートマネージャー（実績報告書をデフォルト）
    const reportManager = useFactoryReportManager('performance_report');

    // CSVファイル管理
    const [csvFiles, setCsvFiles] = useState<Record<string, File | null>>({});
    const [validationResults, setValidationResults] = useState<Record<string, 'valid' | 'invalid' | 'unknown'>>({});

    // 現在の設定を取得
    const currentConfig = reportManager.getCurrentReportConfig();

    // CSVアップロードとバリデーション状態に基づくステップ自動進行
    useEffect(() => {
        const requiredCsvs = currentConfig.csvConfigs.filter(config => config.required);
        const allRequiredUploaded = requiredCsvs.every(config => csvFiles[config.config.label]);
        const allRequiredValid = requiredCsvs.every(config =>
            validationResults[config.config.label] === 'valid'
        );

        if (allRequiredUploaded && allRequiredValid) {
            // 必要なCSVがすべてアップロードされ、バリデーションも通った場合
            if (reportManager.currentStep < 2) {
                reportManager.setCurrentStep(2); // 「帳簿生成」ステップに進む
            }
        } else if (allRequiredUploaded) {
            // CSVはアップロードされているが、バリデーション中・失敗の場合
            if (reportManager.currentStep < 1) {
                reportManager.setCurrentStep(1); // 「CSV準備」ステップのまま
            }
        } else {
            // まだCSVがアップロードされていない場合
            if (reportManager.currentStep > 1) {
                reportManager.setCurrentStep(1); // 「CSV準備」ステップに戻る
            }
        }
    }, [csvFiles, validationResults, currentConfig.csvConfigs, reportManager]);

    // 簡易バリデーション（実際の実装ではより詳細な検証が必要）
    const validateCsv = (file: File): 'valid' | 'invalid' | 'unknown' => {
        if (!file) return 'unknown';

        // ファイル拡張子チェック
        if (!file.name.toLowerCase().endsWith('.csv')) {
            return 'invalid';
        }

        // ファイルサイズチェック（例：10MB以下）
        if (file.size > 10 * 1024 * 1024) {
            return 'invalid';
        }

        // 他のバリデーションロジックをここに追加
        return 'valid';
    };

    // ReportManagePageLayoutに適した形でpropsを作成
    const createUploadFiles = () => {
        return currentConfig.csvConfigs.map((csvConfig: FactoryCsvConfigEntry) => ({
            label: csvConfig.config.label,
            file: csvFiles[csvConfig.config.label] || null,
            onChange: (file: File | null) => {
                setCsvFiles(prev => ({
                    ...prev,
                    [csvConfig.config.label]: file,
                }));

                // ファイルアップロード時にバリデーションを実行
                if (file) {
                    const validationResult = validateCsv(file);
                    setValidationResults(prev => ({
                        ...prev,
                        [csvConfig.config.label]: validationResult,
                    }));
                } else {
                    setValidationResults(prev => ({
                        ...prev,
                        [csvConfig.config.label]: 'unknown',
                    }));
                }
            },
            required: csvConfig.required,
            validationResult: validationResults[csvConfig.config.label] || 'unknown',
            onRemove: () => {
                setCsvFiles(prev => ({
                    ...prev,
                    [csvConfig.config.label]: null,
                }));
                setValidationResults(prev => ({
                    ...prev,
                    [csvConfig.config.label]: 'unknown',
                }));
            },
        }));
    };

    const makeUploadProps = (label: string, setter: (file: File) => void) => ({
        name: 'file',
        multiple: false,
        beforeUpload: (file: File) => {
            setter(file);

            // ファイル状態を更新
            setCsvFiles(prev => ({
                ...prev,
                [label]: file,
            }));

            // バリデーション実行
            const validationResult = validateCsv(file);
            setValidationResults(prev => ({
                ...prev,
                [label]: validationResult,
            }));

            return false; // ファイルアップロードを停止
        },
        onRemove: () => {
            setCsvFiles(prev => ({
                ...prev,
                [label]: null,
            }));
            setValidationResults(prev => ({
                ...prev,
                [label]: 'unknown',
            }));
        },
    });

    // バックエンドAPI連携での帳簿生成
    const handleGenerate = async () => {
        try {
            reportManager.setCurrentStep(3); // 「帳簿生成」→「結果確認」ステップに進む

            // FormDataを作成してCSVファイルを含める
            const formData = new FormData();
            formData.append('reportKey', reportManager.selectedReport);
            formData.append('reportType', currentConfig.type);

            // 実際のCSVファイルを追加
            Object.entries(csvFiles).forEach(([label, file]) => {
                if (file) {
                    formData.append('csvFiles', file, `${label}.csv`);
                }
            });

            // バックエンドAPIへリクエスト（設定ファイルからエンドポイントを取得）
            const apiUrl = factoryReportApiUrlMap[reportManager.selectedReport];
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
            reportManager.setCurrentStep(4); // 「完了」ステップ

            // ZIP URLを保存（ダウンロード用）
            sessionStorage.setItem('lastGeneratedFactoryZip', zipUrl);

        } catch (error) {
            console.error('Factory report generation error:', error);
            reportManager.setCurrentStep(2); // エラー時は「帳簿生成」ステップに戻る
        }
    };

    // 生成準備完了チェック
    const readyToCreate = currentConfig.csvConfigs
        .filter((config: FactoryCsvConfigEntry) => config.required)
        .every((config: FactoryCsvConfigEntry) =>
            csvFiles[config.config.label] &&
            validationResults[config.config.label] === 'valid'
        );

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
                        工場帳簿システム 🏭
                    </h2>
                    <Select
                        value={reportManager.selectedReport}
                        onChange={(value: FactoryReportKey) => reportManager.changeReport(value)}
                        style={{ width: 200 }}
                        options={Object.entries(FACTORY_REPORT_KEYS).map(([key, config]) => ({
                            value: key,
                            label: config.label,
                        }))}
                    />
                </Space>

                {/* 右側：ステッパー（4ステップ対応） */}
                <div style={{ minWidth: 350 }}>
                    <Steps
                        current={reportManager.currentStep - 1}
                        size="small"
                        items={[
                            { title: 'CSV準備' },
                            { title: 'CSV確認' },
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
                const zipUrl = sessionStorage.getItem('lastGeneratedFactoryZip');
                if (zipUrl) {
                    const a = document.createElement('a');
                    a.href = zipUrl;
                    a.download = `工場帳簿_${reportManager.selectedReport}_${Date.now()}.zip`;
                    a.click();
                }
            }}
            onPrintPdf={() => {
                // PDF印刷処理（実装が必要）
                console.log('PDF print');
            }}
            finalized={reportManager.currentStep === 4}
            readyToCreate={readyToCreate}
            pdfUrl={null} // 実装が必要
            excelUrl={sessionStorage.getItem('lastGeneratedFactoryZip')}
            excelReady={!!sessionStorage.getItem('lastGeneratedFactoryZip')}
            pdfReady={false} // 実装が必要
            sampleImageUrl={currentConfig.previewImage}
        >
            <div style={{
                padding: 20,
                textAlign: 'center',
                backgroundColor: '#f6f6f6',
                borderRadius: 8
            }}>
                <h3>工場帳簿プレビュー</h3>
                <p>選択された帳簿: {reportManager.getCurrentReportDefinition().label}</p>
                <p>ステップ: {reportManager.currentStep}/4</p>
                <div style={{ marginTop: 12 }}>
                    <p><strong>CSVアップロード状況:</strong></p>
                    {currentConfig.csvConfigs.map((config: FactoryCsvConfigEntry) => (
                        <div key={config.config.label} style={{ marginBottom: 4 }}>
                            <span>{config.config.label}: </span>
                            {csvFiles[config.config.label] ? (
                                <span style={{ color: validationResults[config.config.label] === 'valid' ? '#52c41a' : '#ff4d4f' }}>
                                    {validationResults[config.config.label] === 'valid' ? '✅ 有効' : '❌ 無効'}
                                </span>
                            ) : (
                                <span style={{ color: '#d9d9d9' }}>📁 未アップロード</span>
                            )}
                        </div>
                    ))}
                </div>
                {!!sessionStorage.getItem('lastGeneratedFactoryZip') && (
                    <p style={{ color: '#52c41a', fontWeight: 600 }}>
                        ✅ ZIP形式のレポートが生成されました
                    </p>
                )}
            </div>
        </ReportManagePageLayout>
    );
};

export default ReportFactory;
