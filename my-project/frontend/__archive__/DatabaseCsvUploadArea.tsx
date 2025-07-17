import React, { useState } from 'react';
import CsvUploadPanel from '@/components/common/csv-upload/CsvUploadPanel';
import { CSV_DEFINITIONS, CsvType } from '@/constants/csvTypes';
import { isCsvMatch } from '@/utils/validators/csvValidator';

const CSV_TYPES: CsvType[] = [
    'shipment',
    'receive',
    'yard',
    'payable',
    'sales_summary',
];

const DatabaseCsvUploadArea: React.FC = () => {
    const [files, setFiles] = useState<Record<CsvType, File | null>>(
        () =>
            Object.fromEntries(CSV_TYPES.map((type) => [type, null])) as Record<
                CsvType,
                File | null
            >
    );
    const [validationResults, setValidationResults] = useState<
        Record<CsvType, 'valid' | 'invalid' | 'unknown'>
    >(
        () =>
            Object.fromEntries(
                CSV_TYPES.map((type) => [type, 'unknown'])
            ) as Record<CsvType, 'valid' | 'invalid' | 'unknown'>
    );

    const handleRemoveFile = (type: CsvType) => {
        setFiles((prev) => ({ ...prev, [type]: null }));
        setValidationResults((prev) => ({ ...prev, [type]: 'unknown' }));
    };

    const makeUploadProps = (type: CsvType) => ({
        accept: '.csv',
        showUploadList: false,
        beforeUpload: (file: File) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target?.result as string;
                const isValid = isCsvMatch(type, text);
                setValidationResults((prev) => ({
                    ...prev,
                    [type]: isValid ? 'valid' : 'invalid',
                }));
                setFiles((prev) => ({
                    ...prev,
                    [type]: isValid ? file : null,
                }));
            };
            reader.readAsText(file);
            return false;
        },
    });

    const panelFiles = CSV_TYPES.map((type) => ({
        label: CSV_DEFINITIONS[type].label,
        file: files[type],
        required: false,
        onChange: (f: File | null) => {
            if (f === null) handleRemoveFile(type);
        },
        validationResult: validationResults[type],
        onRemove: () => handleRemoveFile(type),
        uploadProps: makeUploadProps(type),
    }));

    return (
        <CsvUploadPanel
            upload={{
                files: panelFiles,
                makeUploadProps: (_label, _onChange) => ({}), // uploadPropsを上で渡している場合は空でもOK
            }}
        />
    );
};

export default DatabaseCsvUploadArea;
