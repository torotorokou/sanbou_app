// src/parsers/csvParsers.ts
export const parseReceiveCSV = (text: string) => {
    console.log('💎 受入CSV parsed', text);
};

export const parseShipmentCSV = (text: string) => {
    console.log('🚚 出荷CSV parsed', text);
};

export const parseYardCSV = (text: string) => {
    console.log('👷‍♂️ ヤードCSV parsed', text);
};
