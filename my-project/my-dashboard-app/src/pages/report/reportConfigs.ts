// /app/src/pages/report/reportConfigs.ts

// 各CSVをパースする仮関数（実際にはそれぞれ整備すべき）
const parseValuableCSV = (text: string) => {
    console.log('💎 受入CSV parsed', text);
};

const parseShipmentCSV = (text: string) => {
    console.log('🚚 出荷CSV parsed', text);
};

const parseWorkerCSV = (text: string) => {
    console.log('👷‍♂️ ヤードCSV parsed', text);
};

const parseAttendanceCSV = (text: string) => {
    console.log('🕒 出勤CSV parsed', text);
};

// 帳票設定
export const factoryConfig = {
    reportKey: 'factory',
    csvConfigs: [
        { label: '出荷CSV', onParse: parseShipmentCSV },
        { label: 'ヤードCSV', onParse: parseWorkerCSV },
    ],
    steps: ['データ選択', 'PDF生成中', '完了'],
    generatePdf: async () => '/factory_report.pdf',
};

export const attendanceConfig = {
    reportKey: 'attendance',
    csvConfigs: [
        { label: '受入CSV', onParse: parseValuableCSV },
        { label: '出荷CSV', onParse: parseShipmentCSV },
        { label: 'ヤードCSV', onParse: parseWorkerCSV },
    ],
    steps: ['CSV読み込み', '帳票作成中', '完了'],
    generatePdf: async () => '/attendance_report.pdf',
};

// 必要に応じて他の帳票もここに追加可能
