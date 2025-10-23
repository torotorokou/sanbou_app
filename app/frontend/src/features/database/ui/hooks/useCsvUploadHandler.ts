import { useState } from 'react';
import {
    notifySuccess,
    notifyError,
    notifyInfo,
    notifyWarning,
} from '@features/notification';
import { coreApi } from '@shared/infrastructure/http/coreApi';
import { ApiError } from '@shared/infrastructure/http/httpClient';

export const useCsvUploadHandler = (files: Record<string, File | null>) => {
    const [uploading, setUploading] = useState(false);

    const handleUpload = async () => {
        if (!files) return;

        const formData = new FormData();
        Object.entries(files).forEach(([type, file]) => {
            if (file) formData.append(type, file);
        });

        setUploading(true);

        try {
            // サーバー仕様に合わせたジェネリックなレスポンス型
            interface UploadFileIssue {
                filename?: string;
                status?: string;
                detail?: string;
            }
            interface UploadResponseShape {
                status?: string;
                detail?: string;
                hint?: string;
                result?: Record<string, UploadFileIssue>;
            }

            const result = await coreApi.uploadForm<UploadResponseShape>(
                '/core_api/database/upload/syogun_csv',
                formData,
                { timeout: 60000 }
            );

            if (result.status === 'success') {
                notifySuccess('アップロード成功', result.detail ?? 'CSVを受け付けました。');
                if (result.hint) {
                    notifyInfo('ヒント', result.hint);
                }
            } else {
                notifyError(
                    'アップロード失敗',
                    result?.detail ?? 'アップロード中にエラーが発生しました。'
                );

                if (result?.hint) {
                    notifyInfo('ヒント', result.hint);
                }

                const issues = result?.result;
                if (issues) {
                    Object.entries(issues).forEach(([key, val]) => {
                        if (val?.status === 'error') {
                            notifyWarning(
                                `[${val.filename ?? key}] のエラー`,
                                val.detail ?? '詳細不明のエラーが発生しました。'
                            );
                        }
                    });
                }
            }
        } catch (error) {
            if (error instanceof ApiError) {
                notifyError('アップロードエラー', error.userMessage);
            } else {
                notifyError(
                    '接続エラー',
                    'サーバーに接続できませんでした。ネットワークを確認してください。'
                );
            }
        } finally {
            setUploading(false);
        }
    };

    return { uploading, handleUpload };
};
