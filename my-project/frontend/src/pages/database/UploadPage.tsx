// src/pages/UploadPage.tsx
import React, { useState } from 'react';
import { Upload, Button, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import axios from 'axios';

const UploadPage: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);

    const handleUpload = async () => {
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        try {
            await axios.post('/api/data/upload_csv', formData);
            message.success('アップロード成功');
        } catch (error) {
            message.error('アップロード失敗');
        }
    };

    return (
        <div>
            <h2>CSVアップロード</h2>
            <Upload
                beforeUpload={(f) => {
                    setFile(f);
                    return false;
                }}
                showUploadList={false}
            >
                <Button icon={<UploadOutlined />}>ファイルを選択</Button>
            </Upload>
            <Button type='primary' onClick={handleUpload} disabled={!file}>
                アップロード
            </Button>
        </div>
    );
};

export default UploadPage;
