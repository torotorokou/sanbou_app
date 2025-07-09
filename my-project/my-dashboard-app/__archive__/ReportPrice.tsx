import React, { useState } from 'react';
import { ConfigProvider } from 'antd';
import jaJP from 'antd/locale/ja_JP';
import dayjs, { Dayjs } from 'dayjs';
import 'dayjs/locale/ja';
import ReportManagePageLayout from '@/components/Report/common/ReportManagePageLayout';
import type { UploadProps } from 'antd';
import type { ColumnsType } from 'antd/es/table';

dayjs.locale('ja');

type ReportRow = {
    key: string;
    工場: string;
    搬入量: number;
    搬出量: number;
};

const columns: ColumnsType<ReportRow> = [
    { title: '工場', dataIndex: '工場', key: '工場' },
    { title: '搬入量', dataIndex: '搬入量', key: '搬入量' },
    { title: '搬出量', dataIndex: '搬出量', key: '搬出量' },
];

const ReportFactory: React.FC = () => {
    const [selectedDate, setSelectedDate] = useState<Dayjs | null>(null);
    const [shipFile, setShipFile] = useState<File | null>(null);
    const [yardFile, setYardFile] = useState<File | null>(null);
    const [receiveFile, setReceiveFile] = useState<File | null>(null);
    const [csvData, setCsvData] = useState<ReportRow[]>([]);
    const [finalized, setFinalized] = useState(false);

    const makeUploadProps = (
        label: string,
        setter: (file: File) => void
    ): UploadProps => ({
        accept: '.csv',
        showUploadList: false,
        beforeUpload: (file) => {
            setter(file);
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target?.result as string;
                const rows = text.split('\n').map((row) => row.split(','));
                const data: ReportRow[] = rows
                    .slice(1)
                    .filter((r) => r.length >= 3)
                    .map((cols, i) => ({
                        key: i.toString(),
                        工場: cols[0],
                        搬入量: parseFloat(cols[1]),
                        搬出量: parseFloat(cols[2]),
                    }));
                setCsvData(data);
            };
            reader.readAsText(file);
            return false;
        },
    });

    const handleGenerate = () => {
        setFinalized(true);
    };

    return (
        <ConfigProvider locale={jaJP}>
            <ReportManagePageLayout
                title='📅 工場日報'
                onGenerate={handleGenerate}
                calendarDate={selectedDate}
                onDateChange={setSelectedDate}
                uploadFiles={[
                    { label: '出荷CSV', file: shipFile, onChange: setShipFile },
                    {
                        label: 'ヤードCSV',
                        file: yardFile,
                        onChange: setYardFile,
                    },
                    {
                        label: '受入CSV',
                        file: receiveFile,
                        onChange: setReceiveFile,
                    },
                ]}
                makeUploadProps={makeUploadProps}
                tableData={csvData}
                tableColumns={columns}
                finalized={finalized}
            />
        </ConfigProvider>
    );
};

export default ReportFactory;
