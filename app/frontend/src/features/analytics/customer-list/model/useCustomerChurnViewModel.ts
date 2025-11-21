/**
 * Customer Churn ViewModel - Main Orchestrator
 * 
 * 4つのサブフィーチャーを統合し、顧客離脱分析のメインロジックを提供
 */

import { useState } from 'react';
import { message } from 'antd';
import type { Dayjs } from 'dayjs';
import type { CustomerData } from '../domain/types';

// Sub-features
import { usePeriodSelector, isValidPeriodRange, getMonthRange } from '../period-selector';
import { aggregateCustomers } from '../customer-aggregation';
import { useCustomerComparison } from '../customer-comparison';
import { useExcelDownload, buildCustomerCsv, downloadCsv } from '../data-export';

// Mock Data (TODO: 将来的にAPIに置き換え)
import { generateMockResponse } from './mockData';

export interface CustomerChurnViewModel {
    // Period Selection
    currentStart: Dayjs | null;
    currentEnd: Dayjs | null;
    previousStart: Dayjs | null;
    previousEnd: Dayjs | null;
    setCurrentStart: (date: Dayjs | null) => void;
    setCurrentEnd: (date: Dayjs | null) => void;
    setPreviousStart: (date: Dayjs | null) => void;
    setPreviousEnd: (date: Dayjs | null) => void;
    
    // Data Loading
    isLoading: boolean;
    isAnalyzing: boolean;
    analysisStarted: boolean;
    dataSource: CustomerData[];
    
    // Customer Data
    currentCustomers: CustomerData[];
    previousCustomers: CustomerData[];
    
    // Customer Comparison
    lostCustomers: CustomerData[];
    commonCustomers: CustomerData[];
    newCustomers: CustomerData[];
    
    // UI State
    isButtonDisabled: boolean;
    downloadingExcel: boolean;
    
    // Actions
    handleSearch: () => Promise<void>;
    handleAnalyze: () => Promise<void>;
    handleDownloadLostCsv: () => void;
    handleDownloadLostCustomersCsv: () => void;
    resetConditions: () => void;
    
    // Excel Export
    isDownloading: boolean;
    handleDownloadExcel: () => Promise<void>;
}

/**
 * 顧客離脱分析の主ViewModel
 * 
 * @param apiPostBlob - API呼び出し関数（DI）
 */
export function useCustomerChurnViewModel(
    apiPostBlob: <T>(url: string, data: T) => Promise<Blob>
): CustomerChurnViewModel {
    // Sub-feature: Period Selection
    const {
        currentStart,
        currentEnd,
        previousStart,
        previousEnd,
        setCurrentStart,
        setCurrentEnd,
        setPreviousStart,
        setPreviousEnd,
    } = usePeriodSelector();
    
    // Sub-feature: Excel Download
    const { isDownloading, handleDownload: handleExcelDownload } = useExcelDownload(apiPostBlob);
    
    // Data Loading
    const [isLoading, setIsLoading] = useState(false);
    const [analysisStarted, setAnalysisStarted] = useState(false);
    const [currentData, setCurrentData] = useState<CustomerData[]>([]);
    const [previousData, setPreviousData] = useState<CustomerData[]>([]);
    
    // Sub-feature: Customer Comparison
    const { lostCustomers, retainedCustomers, newCustomers } = useCustomerComparison(currentData, previousData);
    
    // Combine all data for display
    const dataSource = [...currentData, ...previousData];
    
    /**
     * 検索処理
     * 
     * TODO: 現在はモックデータを使用。将来的にapiPostBlobでバックエンドAPIと連携
     */
    const handleSearch = async (): Promise<void> => {
        if (!isValidPeriodRange(currentStart, currentEnd) || !isValidPeriodRange(previousStart, previousEnd)) {
            message.error('有効な期間を選択してください');
            return;
        }
        
        setIsLoading(true);
        try {
            // 期間から月リストを生成
            const currentMonths = getMonthRange(currentStart!, currentEnd!);
            const previousMonths = getMonthRange(previousStart!, previousEnd!);
            
            // TODO: 将来的にはこのコードに置き換え
            /*
            const blob = await apiPostBlob<Record<string, string | undefined>>(
                '/core_api/customer-comparison',
                {
                    targetStart: currentStart?.format('YYYY-MM'),
                    targetEnd: currentEnd?.format('YYYY-MM'),
                    compareStart: previousStart?.format('YYYY-MM'),
                    compareEnd: previousEnd?.format('YYYY-MM'),
                }
            );
            const text = await blob.text();
            const data = JSON.parse(text);
            */
            
            // 暫定: モックデータを使用
            await new Promise(resolve => setTimeout(resolve, 800)); // 読み込み感を演出
            const data = generateMockResponse(currentMonths, previousMonths);
            
            // Parse API response into current/previous data
            const monthlyData: Record<string, CustomerData[]> = data.results || {};
            
            // Sub-feature: Customer Aggregation
            const aggregatedCurrent = aggregateCustomers(currentMonths, monthlyData);
            const aggregatedPrevious = aggregateCustomers(previousMonths, monthlyData);
            
            setCurrentData(aggregatedCurrent);
            setPreviousData(aggregatedPrevious);
            setAnalysisStarted(true);
            
            message.success('分析が完了しました');
        } catch (error) {
            console.error('Analysis error:', error);
            message.error('データ取得に失敗しました');
        } finally {
            setIsLoading(false);
        }
    };
    
    /**
     * 条件リセット
     */
    const resetConditions = (): void => {
        setCurrentStart(null);
        setCurrentEnd(null);
        setPreviousStart(null);
        setPreviousEnd(null);
        setCurrentData([]);
        setPreviousData([]);
        setAnalysisStarted(false);
    };
    
    /**
     * ボタンの有効/無効判定
     */
    const isButtonDisabled = !currentStart || !currentEnd || !previousStart || !previousEnd;
    
    /**
     * 離脱顧客のCSVダウンロード
     */
    const handleDownloadLostCsv = (): void => {
        if (lostCustomers.length === 0) {
            message.warning('離脱顧客がありません');
            return;
        }
        
        // Sub-feature: Data Export (CSV)
        const csvContent = buildCustomerCsv(lostCustomers);
        const filename = `離脱顧客リスト_${currentStart?.format('YYYYMM')}-${currentEnd?.format('YYYYMM')}.csv`;
        downloadCsv(csvContent, filename);
        message.success('CSVをダウンロードしました');
    };
    
    /**
     * Excelダウンロード
     */
    const handleDownloadExcel = async (): Promise<void> => {
        await handleExcelDownload(currentStart, currentEnd, previousStart, previousEnd);
    };
    
    return {
        // Period Selection
        currentStart,
        currentEnd,
        previousStart,
        previousEnd,
        setCurrentStart,
        setCurrentEnd,
        setPreviousStart,
        setPreviousEnd,
        
        // Data Loading
        isLoading,
        isAnalyzing: isLoading,
        analysisStarted,
        dataSource,
        
        // Customer Data
        currentCustomers: currentData,
        previousCustomers: previousData,
        
        // Customer Comparison
        lostCustomers,
        commonCustomers: retainedCustomers,
        newCustomers,
        
        // UI State
        isButtonDisabled,
        downloadingExcel: isDownloading,
        
        // Actions
        handleSearch,
        handleAnalyze: handleSearch,
        handleDownloadLostCsv,
        handleDownloadLostCustomersCsv: handleDownloadLostCsv,
        resetConditions,
        
        // Excel Export
        isDownloading,
        handleDownloadExcel,
    };
}
