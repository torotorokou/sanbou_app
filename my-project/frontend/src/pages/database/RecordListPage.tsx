// src/pages/RecordListPage.tsx
import React, { useEffect, useState } from 'react';
import { Table, message } from 'antd';
import axios from 'axios';

type RecordType = {
    id: number;
    name: string;
    amount: number;
};

const RecordListPage: React.FC = () => {
    const [data, setData] = useState<RecordType[]>([]);

    useEffect(() => {
        axios
            .get('/api/data/list')
            .then((res) => {
                if (Array.isArray(res.data)) {
                    setData(res.data);
                } else {
                    message.error('データ形式が不正です');
                }
            })
            .catch(() => message.error('データ取得に失敗'));
    }, []);

    const columns = [
        { title: 'ID', dataIndex: 'id' },
        { title: '名前', dataIndex: 'name' },
        { title: '金額', dataIndex: 'amount' },
    ];

    return (
        <div>
            <h2>データ一覧</h2>
            <Table columns={columns} dataSource={data} rowKey='id' />
        </div>
    );
};

export default RecordListPage;
