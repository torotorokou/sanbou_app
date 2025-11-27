import { client } from '@features/report/shared/api/http.adapter';

export const downloadExcelFile = async (
    reportKey: string,
    files: { [label: string]: File | null }
) => {
    try {
        const formData = new FormData();
        Object.entries(files).forEach(([label, fileObj]) => {
            if (fileObj) formData.append(label, fileObj);
        });
        formData.append('report_key', reportKey);
        
        // Blob レスポンスのため直接 client を使用
        const response = await client.post('/core_api/reports/excel', formData, {
            responseType: 'blob',
            timeout: 60000,
        });

        const blob = response.data as Blob;
        let filename = 'report.xlsx';
        const disposition = response.headers['content-disposition'];
        if (disposition) {
            const match = disposition.match(/filename="?([^"]+)"?/);
            if (match) filename = match[1];
        }
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    } catch {
        // TODO: ログ送信などを追加可能
        alert('Excelのダウンロードに失敗しました');
    }
};
