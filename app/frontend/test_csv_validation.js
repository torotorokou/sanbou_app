import { identifyCsvType, isCsvMatch } from '../utils/validators/csvValidator';

// テスト用のCSVヘッダー
const validShipmentHeaders = [
    '伝票日付',
    '出荷番号',
    '取引先名',
    '業者CD',
    '業者名',
];
const validYardHeaders = ['伝票日付', '取引先名', '品名', '正味重量', '数量'];
const invalidHeaders = ['日付', '番号', '会社名', 'コード', '名前'];

console.log('=== CSV検証システムテスト ===');

// shipmentタイプの検証テスト
console.log('\n1. 出荷CSVの検証:');
const shipmentType = identifyCsvType(validShipmentHeaders);
console.log(`識別結果: ${shipmentType}`);
console.log(`マッチング: ${isCsvMatch(validShipmentHeaders, 'shipment')}`);

// yardタイプの検証テスト
console.log('\n2. ヤードCSVの検証:');
const yardType = identifyCsvType(validYardHeaders);
console.log(`識別結果: ${yardType}`);
console.log(`マッチング: ${isCsvMatch(validYardHeaders, 'yard')}`);

// 無効なヘッダーのテスト
console.log('\n3. 無効ヘッダーの検証:');
const invalidType = identifyCsvType(invalidHeaders);
console.log(`識別結果: ${invalidType}`);
console.log(`shipmentマッチング: ${isCsvMatch(invalidHeaders, 'shipment')}`);
console.log(`yardマッチング: ${isCsvMatch(invalidHeaders, 'yard')}`);

// クロスチェック（shipmentヘッダーでyardを検証）
console.log('\n4. クロスチェック:');
console.log(
    `shipmentヘッダーでyard検証: ${isCsvMatch(validShipmentHeaders, 'yard')}`
);
console.log(
    `yardヘッダーでshipment検証: ${isCsvMatch(validYardHeaders, 'shipment')}`
);
