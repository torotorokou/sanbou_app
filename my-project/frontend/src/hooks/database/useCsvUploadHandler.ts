import { useState } from 'react';
import {
    notifySuccess,
    notifyError,
    notifyInfo,
    notifyWarning,
} from '@/utils/notify';

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
            const res = await fetch('/sql_api/upload/syogun_csv', {
                method: 'POST',
                body: formData,
            });

            const text = await res.text();
            let result: any;
            try {
                result = JSON.parse(text);
            } catch {
                notifyError(
                    'サーバーエラー',
                    `サーバー応答がJSONではありません: ${text}`
                );
                return;
            }

            if (res.ok && result.status === 'success') {
                notifySuccess(
                    'アップロード成功',
                    result.detail ?? 'CSVファイルのアップロードが完了しました。'
                );
            } else {
                notifyError(
                    'アップロード失敗',
                    result?.detail ?? 'アップロード中にエラーが発生しました。'
                );

                if (result?.hint) {
                    notifyInfo('ヒント', result.hint);
                }

                if (result?.result) {
                    Object.entries(result.result).forEach(
                        ([key, val]: [string, any]) => {
                            if (val.status === 'error') {
                                notifyWarning(
                                    `[${val.filename ?? key}] のエラー`,
                                    val.detail ??
                                        '詳細不明のエラーが発生しました。'
                                );
                            }
                        }
                    );
                }
            }
        } catch (err) {
            notifyError(
                '接続エラー',
                'サーバーに接続できませんでした。ネットワークを確認してください。'
            );
        } finally {
            setUploading(false);
        }
    };

    return { uploading, handleUpload };
};
