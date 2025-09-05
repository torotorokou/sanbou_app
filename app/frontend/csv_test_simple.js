// 簡単なCSV検証テスト
const fs = require('fs');
const path = require('path');

// CSVテストファイルの内容を確認
console.log('=== CSVファイル検証テスト ===\n');

const testFiles = [
    { name: '出荷CSV（正常）', file: 'test_shipment_valid.csv' },
    { name: 'ヤードCSV（正常）', file: 'test_yard_valid.csv' },
    { name: '受入CSV（正常）', file: 'test_receive_valid.csv' },
    { name: '出荷CSV（異常）', file: 'test_shipment_invalid.csv' },
];

testFiles.forEach(({ name, file }) => {
    try {
        const content = fs.readFileSync(
            path.join(__dirname, 'public', file),
            'utf8'
        );
        const headers = content
            .split('\n')[0]
            .split(',')
            .map((h) => h.trim());

        console.log(`${name}:`);
        console.log(`  ファイル: ${file}`);
        console.log(`  ヘッダー: [${headers.join(', ')}]`);
        console.log('');
    } catch (error) {
        console.log(`${name}: ファイル読み込みエラー - ${error.message}\n`);
    }
});

// YAML設定で期待されるヘッダー
console.log('=== 期待されるヘッダー（YAML設定より） ===');
console.log('出荷一覧: [伝票日付, 出荷番号, 取引先名, 業者CD, 業者名]');
console.log('ヤード一覧: [伝票日付, 取引先名, 品名, 正味重量, 数量]');
console.log('受入一覧: [伝票日付, 売上日付, 支払日付, 業者CD, 業者名]');
