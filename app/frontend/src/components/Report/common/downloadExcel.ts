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
        const response = await fetch('/api/report/excel', {
            method: 'POST',
            body: formData,
        });
        if (!response.ok) throw new Error('Excel出力失敗');
        const blob = await response.blob();

        let filename = 'report.xlsx';
        const disposition = response.headers.get('Content-Disposition');
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
