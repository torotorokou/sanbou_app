export type WorkerRow = {
    key: string;
    氏名: string;
    所属: string;
    出勤区分: string;
};

export type ValuableRow = {
    key: string;
    品目: string;
    重量: number;
    単価: number;
};

export type ShipmentRow = {
    key: string;
    商品名: string;
    出荷先: string;
    数量: number;
};
