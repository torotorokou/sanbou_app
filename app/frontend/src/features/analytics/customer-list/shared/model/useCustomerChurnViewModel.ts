/**
 * Customer Churn ViewModel - Main Orchestrator
 * 
 * Repository パターンを使用して顧客離脱分析のメインロジックを提供
 */

import { useState, useEffect } from 'react';
import { message } from 'antd';
import type { Dayjs } from 'dayjs';
import type { CustomerData, LostCustomer, SalesRep } from '../domain/types';
import { customerChurnRepository } from '../infrastructure/customerChurnRepository';

// Sub-features
import { usePeriodSelector, isValidPeriodRange } from '../../period-selector';
import { buildCustomerCsv, downloadCsv } from '../../data-export';

/**
 * LostCustomer を CustomerData に変換
 */
function mapLostCustomerToCustomerData(lost: LostCustomer): CustomerData {
    return {
        key: lost.customerId,
        name: lost.customerName,
        weight: lost.prevTotalQtyKg,
        amount: lost.prevTotalAmountYen,
        sales: lost.salesRepName || '不明',
        lastDeliveryDate: lost.lastVisitDate,
    };
}

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
    
    // Sales Rep Filter
    salesReps: SalesRep[];
    selectedSalesRepIds: string[];
    setSelectedSalesRepIds: (ids: string[]) => void;
    
    // Data Loading
    isLoading: boolean;
    isAnalyzing: boolean;
    analysisStarted: boolean;
    
    // Customer Comparison (filtered)
    lostCustomers: CustomerData[];
    
    // UI State
    isButtonDisabled: boolean;
    
    // Actions
    handleAnalyze: () => Promise<void>;
    handleDownloadLostCustomersCsv: () => void;
    resetConditions: () => void;
}

/**
 * 顧客離脱分析の主ViewModel
 * 
 * Repository パターンを使用してバックエンドAPIと連携
 */
export function useCustomerChurnViewModel(): CustomerChurnViewModel {
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
    
    // Sales Rep Filter
    const [salesReps, setSalesReps] = useState<SalesRep[]>([]);
    const [selectedSalesRepIds, setSelectedSalesRepIds] = useState<string[]>([]);
    
    // Data Loading
    const [isLoading, setIsLoading] = useState(false);
    const [analysisStarted, setAnalysisStarted] = useState(false);
    const [lostCustomersData, setLostCustomersData] = useState<CustomerData[]>([]);
    const [allLostCustomersData, setAllLostCustomersData] = useState<CustomerData[]>([]);
    
    // Load sales reps on mount
    useEffect(() => {
        const loadSalesReps = async () => {
            try {
                const reps = await customerChurnRepository.getSalesReps();
                setSalesReps(reps);
            } catch (error) {
                console.error('Failed to load sales reps:', error);
                message.error('営業担当者リストの取得に失敗しました');
            }
        };
        loadSalesReps();
    }, []);
    
    // Filter lost customers by selected sales reps
    useEffect(() => {
        if (selectedSalesRepIds.length === 0) {
            setLostCustomersData(allLostCustomersData);
        } else {
            const filtered = allLostCustomersData.filter(customer => 
                selectedSalesRepIds.some(id => {
                    const rep = salesReps.find(r => r.salesRepId === id);
                    return rep && customer.sales === rep.salesRepName;
                })
            );
            setLostCustomersData(filtered);
        }
    }, [selectedSalesRepIds, allLostCustomersData, salesReps]);
    
    /**
     * 分析処理（Repository経由でバックエンドAPIを呼び出し）
     */
    const handleAnalyze = async (): Promise<void> => {
        if (!isValidPeriodRange(currentStart, currentEnd) || !isValidPeriodRange(previousStart, previousEnd)) {
            message.error('有効な期間を選択してください');
            return;
        }
        
        setIsLoading(true);
        try {
            // 月の選択を日付範囲に変換
            // 開始月 → 月初（1日）、終了月 → 月末（最終日）
            const currentStartDate = currentStart!.startOf('month').format('YYYY-MM-DD');
            const currentEndDate = currentEnd!.endOf('month').format('YYYY-MM-DD');
            const previousStartDate = previousStart!.startOf('month').format('YYYY-MM-DD');
            const previousEndDate = previousEnd!.endOf('month').format('YYYY-MM-DD');
            
            // Repository経由でバックエンドAPIを呼び出し
            const lostCustomers = await customerChurnRepository.analyze({
                currentStart: currentStartDate,
                currentEnd: currentEndDate,
                previousStart: previousStartDate,
                previousEnd: previousEndDate,
            });
            
            // LostCustomer -> CustomerData に変換
            const mappedData = lostCustomers.map(mapLostCustomerToCustomerData);
            setAllLostCustomersData(mappedData);
            setLostCustomersData(mappedData);
            setAnalysisStarted(true);
            
            message.success(`分析が完了しました（離脱顧客: ${lostCustomers.length}件）`);
        } catch (error) {
            console.error('Analysis error:', error);
            message.error('分析に失敗しました');
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
        setLostCustomersData([]);
        setAnalysisStarted(false);
    };
    
    /**
     * ボタンの有効/無効判定
     */
    const isButtonDisabled = !currentStart || !currentEnd || !previousStart || !previousEnd;
    
    /**
     * 離脱顧客のCSVダウンロード
     */
    const handleDownloadLostCustomersCsv = (): void => {
        if (lostCustomersData.length === 0) {
            message.warning('離脱顧客がありません');
            return;
        }
        
        // Sub-feature: Data Export (CSV)
        const csvContent = buildCustomerCsv(lostCustomersData);
        const filename = `離脱顧客リスト_${currentStart?.format('YYYYMMDD')}-${currentEnd?.format('YYYYMMDD')}.csv`;
        downloadCsv(csvContent, filename);
        message.success('CSVをダウンロードしました');
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
        
        // Sales Rep Filter
        salesReps,
        selectedSalesRepIds,
        setSelectedSalesRepIds,
        
        // Data Loading
        isLoading,
        isAnalyzing: isLoading,
        analysisStarted,
        
        // Customer Comparison
        lostCustomers: lostCustomersData,
        
        // UI State
        isButtonDisabled,
        
        // Actions
        handleAnalyze,
        handleDownloadLostCustomersCsv,
        resetConditions,
    };
}
