// src/parsers/csvParsers.ts
export const parseReceiveCSV = (text: string) => {
    console.log('💎 受入一覧 parsed', text);
};

export const parseShipmentCSV = (text: string) => {
    console.log('🚚 出荷一覧 parsed', text);
};

export const parseYardCSV = (text: string) => {
    console.log('👷‍♂️ ヤード一覧 parsed', text);
};
