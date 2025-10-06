import { useState, useMemo } from 'react';
import {
    UPLOAD_CSV_TYPES,
    UPLOAD_CSV_DEFINITIONS,
} from '../model/uploadCsvConfig';
import type { CsvType } from '../model/CsvDefinition';
import { identifyCsvType, isCsvMatch } from '@shared/utils/validators/csvValidator';
import { parseCsvPreview } from '@shared/utils/csv/csvPreview'; // 行数制限プレビュー用

export function useCsvUploadArea() {
    const [files, setFiles] = useState<Record<CsvType, File | null>>(
        () =>
            Object.fromEntries(
                UPLOAD_CSV_TYPES.map((type) => [type, null])
            ) as Record<CsvType, File | null>
    );
    const [validationResults, setValidationResults] = useState<
        Record<CsvType, 'valid' | 'invalid' | 'unknown'>
    >(
        () =>
            Object.fromEntries(
                UPLOAD_CSV_TYPES.map((type) => [type, 'unknown'])
            ) as Record<CsvType, 'valid' | 'invalid' | 'unknown'>
    );
    const [csvPreviews, setCsvPreviews] = useState<
        Record<CsvType, { columns: string[]; rows: string[][] } | null>
    >(
        () =>
            Object.fromEntries(
                UPLOAD_CSV_TYPES.map((type) => [type, null])
            ) as Record<CsvType, { columns: string[]; rows: string[][] } | null>
    );

    const labelToType = useMemo(
        () =>
            Object.fromEntries(
                UPLOAD_CSV_TYPES.map((type) => [
                    UPLOAD_CSV_DEFINITIONS[type].label,
                    type,
                ])
            ) as Record<string, CsvType>,
        []
    );

    function handleCsvFile(label: string, file: File | null) {
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            const text = e.target?.result as string;
            const type = labelToType[label];
            setCsvPreviews((prev) => ({
                ...prev,
                [type]: parseCsvPreview(text),
            }));
            if (!type) {
                setValidationResults((prev) => ({
                    ...prev,
                    [type]: 'invalid',
                }));
                setFiles((prev) => ({ ...prev, [type]: null }));
                return;
            }
            const result = identifyCsvType(text);
            const isValid = isCsvMatch(result, label);
            setValidationResults((prev) => ({
                ...prev,
                [type]: isValid ? 'valid' : 'invalid',
            }));
            setFiles((prev) => ({ ...prev, [type]: file }));
        };
        reader.readAsText(file);
    }

    function removeCsvFile(type: CsvType) {
        setFiles((prev) => ({ ...prev, [type]: null }));
        setValidationResults((prev) => ({ ...prev, [type]: 'unknown' }));
        setCsvPreviews((prev) => ({ ...prev, [type]: null }));
    }

    // 必須判定などは useMemo で
    const requiredTypes = useMemo(
        () =>
            UPLOAD_CSV_TYPES.filter(
                (type) => UPLOAD_CSV_DEFINITIONS[type].required
            ),
        []
    );
    const canUpload = requiredTypes.every(
        (type) => files[type] && validationResults[type] === 'valid'
    );

    return {
        files,
        setFiles,
        validationResults,
        setValidationResults,
        csvPreviews,
        setCsvPreviews,
        canUpload,
        handleCsvFile,
        removeCsvFile,
    };
}
