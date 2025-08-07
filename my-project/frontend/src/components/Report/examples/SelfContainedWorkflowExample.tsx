import React from 'react';
import { Button } from 'antd';
import BlockUnitPriceWorkflowSelfContained from '../individual_process/BlockUnitPriceWorkflowSelfContained';

// 自己完結型ワークフローの使用例
const SelfContainedWorkflowExample: React.FC = () => {
    const [isWorkflowVisible, setIsWorkflowVisible] = React.useState(false);
    const [selectedFile, setSelectedFile] = React.useState<File | undefined>();

    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            setIsWorkflowVisible(true);
        }
    };

    const handleWorkflowComplete = (result: unknown) => {
        console.log('ワークフロー完了:', result);
        // 完了後の処理（例：レポート表示、通知など）
    };

    const handleWorkflowClose = () => {
        setIsWorkflowVisible(false);
        setSelectedFile(undefined);
    };

    return (
        <div className="self-contained-workflow-example">
            <h2>自己完結型インタラクティブレポートの例</h2>

            <div className="upload-section">
                <label htmlFor="csv-upload">
                    <Button type="primary">CSVファイルを選択</Button>
                </label>
                <input
                    id="csv-upload"
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                />
            </div>

            {/* 自己完結型ワークフロー */}
            <BlockUnitPriceWorkflowSelfContained
                visible={isWorkflowVisible}
                onClose={handleWorkflowClose}
                onComplete={handleWorkflowComplete}
                csvFile={selectedFile}
                config={{
                    title: 'ブロック単価レポート処理',
                    steps: [
                        { title: '運搬業者選択', content: '運搬業者を選択してください' },
                        { title: 'データ確認', content: 'データを確認しています' },
                        { title: '処理完了', content: '処理が完了しました' }
                    ]
                }}
            />
        </div>
    );
};

export default SelfContainedWorkflowExample;
