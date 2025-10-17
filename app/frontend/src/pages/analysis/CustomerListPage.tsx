import React, { useState } from 'react';
import { Row, Col, Button, Card, message } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { customTokens } from '@shared/theme/tokens';
import type { Dayjs } from 'dayjs';
import {
  ComparisonConditionForm,
  CustomerComparisonResultCard,
  AnalysisProcessingModal,
} from '@features/analysis';
import { useCustomerComparison } from '@features/analysis/model';
import { apiPostBlob } from '@shared/infrastructure/http';

function getMonthRange(start: Dayjs | null, end: Dayjs | null): string[] {
    if (!start || !end) return [];
    const range: string[] = [];
    let current = start.startOf('month');
    while (
        current.isBefore(end.endOf('month')) ||
        current.isSame(end, 'month')
    ) {
        range.push(current.format('YYYY-MM'));
        current = current.add(1, 'month');
        if (range.length > 24) break;
    }
    return range;
}

const CustomerListAnalysis: React.FC = () => {
    const [targetStart, setTargetStart] = useState<Dayjs | null>(null);
    const [targetEnd, setTargetEnd] = useState<Dayjs | null>(null);
    const [compareStart, setCompareStart] = useState<Dayjs | null>(null);
    const [compareEnd, setCompareEnd] = useState<Dayjs | null>(null);
    const [analysisStarted, setAnalysisStarted] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [downloading, setDownloading] = useState(false);

    const targetMonths = getMonthRange(targetStart, targetEnd);
    const compareMonths = getMonthRange(compareStart, compareEnd);

    const { targetCustomers, compareCustomers, onlyCompare } =
        useCustomerComparison(targetMonths, compareMonths);

    const handleAnalyze = () => {
        setIsAnalyzing(true);
        setAnalysisStarted(false);
        setTimeout(() => {
            setIsAnalyzing(false);
            setAnalysisStarted(true);
        }, 1000);
    };

    const resetConditions = () => {
        setTargetStart(null);
        setTargetEnd(null);
        setCompareStart(null);
        setCompareEnd(null);
        setAnalysisStarted(false);
    };

    // ダウンロードAPIリクエスト
    const handleDownload = async () => {
        if (!analysisStarted) return;
        setDownloading(true);
        try {
            const blob = await apiPostBlob<Record<string, string | undefined>>(
                '/core_api/customer-comparison/excel',
                {
                    targetStart: targetStart?.format('YYYY-MM'),
                    targetEnd: targetEnd?.format('YYYY-MM'),
                    compareStart: compareStart?.format('YYYY-MM'),
                    compareEnd: compareEnd?.format('YYYY-MM'),
                }
            );

            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', '顧客比較リスト.xlsx');
            document.body.appendChild(link);
            link.click();
            link.parentNode?.removeChild(link);
            window.URL.revokeObjectURL(url);
            message.success('エクセルをダウンロードしました');
        } catch {
            message.error('ダウンロードに失敗しました');
        }
        setDownloading(false);
    };

    const isButtonDisabled =
        !targetStart ||
        !targetEnd ||
        !compareStart ||
        !compareEnd ||
        targetEnd.isBefore(targetStart, 'month') ||
        compareEnd.isBefore(compareStart, 'month') ||
        isAnalyzing;

    return (
        <div style={{ height: '100%', minHeight: 0 }}>
            {/* 分析中モーダル */}
            <AnalysisProcessingModal open={isAnalyzing} />

            <Row gutter={24} style={{ height: '100%', minHeight: 0 }}>
                {/* 左カラム */}
                <Col
                    span={7}
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        height: '100%',
                        padding: '40px 24px',
                        background: '#f8fcfa',
                    }}
                >
                    <div
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 32,
                            height: '100%',
                            justifyContent: 'flex-start',
                            alignItems: 'stretch',
                        }}
                    >
                        <Card
                            title='比較条件の選択'
                            bordered={false}
                            style={{
                                boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
                                marginBottom: 24,
                                borderRadius: 16,
                            }}
                            headStyle={{
                                background: '#f0f5ff',
                                fontWeight: 600,
                                borderTopLeftRadius: 16,
                                borderTopRightRadius: 16,
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                            }}
                            extra={
                                <Button
                                    type='primary'
                                    danger
                                    onClick={resetConditions}
                                    size='middle'
                                    icon={<ReloadOutlined />}
                                    style={{ fontWeight: 600 }}
                                >
                                    リセット
                                </Button>
                            }
                        >
                            <ComparisonConditionForm
                                targetStart={targetStart}
                                targetEnd={targetEnd}
                                compareStart={compareStart}
                                compareEnd={compareEnd}
                                setTargetStart={setTargetStart}
                                setTargetEnd={setTargetEnd}
                                setCompareStart={setCompareStart}
                                setCompareEnd={setCompareEnd}
                            />
                        </Card>
                        <Button
                            type='primary'
                            size='large'
                            block
                            disabled={isButtonDisabled}
                            onClick={handleAnalyze}
                            style={{
                                fontWeight: 600,
                                letterSpacing: 1,
                                marginBottom: 16,
                                height: 48,
                            }}
                        >
                            分析する
                        </Button>
                        <Button
                            type='default'
                            size='large'
                            block
                            loading={downloading}
                            disabled={!analysisStarted || downloading}
                            onClick={handleDownload}
                            style={{
                                fontWeight: 600,
                                letterSpacing: 1,
                                height: 48,
                            }}
                        >
                            ダウンロード
                        </Button>
                    </div>
                </Col>

                {/* 右カラム */}
                <Col
                    span={17}
                    style={{
                        height: '95%',
                        minHeight: 0,
                        display: 'flex',
                        flexDirection: 'column',
                    }}
                >
                    {!analysisStarted ? (
                        <div
                            style={{
                                marginTop: 24,
                                color: '#888',
                                height: '100%',
                                minHeight: 0,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            左で月を選択し、「分析する」ボタンを押してください。
                        </div>
                    ) : (
                        <div
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: 12,
                                height: '100%',
                                minHeight: 0,
                                flex: 1,
                            }}
                        >
                            <CustomerComparisonResultCard
                                title='比較月グループにしかいない顧客'
                                data={onlyCompare}
                                cardStyle={{
                                    backgroundColor:
                                        customTokens.colorBgContainer,
                                }}
                                headStyle={{
                                    background:
                                        'linear-gradient(90deg, rgba(244,63,94,0.4), rgba(244,63,94,0.05))',
                                    color: '#333',
                                }}
                                style={{
                                    flex: 4,
                                    minHeight: 0,
                                    display: 'flex',
                                    flexDirection: 'column',
                                }}
                            />

                            <CustomerComparisonResultCard
                                title='対象月グループの顧客'
                                data={targetCustomers}
                                cardStyle={{
                                    backgroundColor:
                                        customTokens.colorBgContainer,
                                }}
                                headStyle={{
                                    background:
                                        'linear-gradient(90deg, rgba(16,185,129,0.4), rgba(16,185,129,0.05))',
                                    color: '#333',
                                }}
                                style={{
                                    flex: 3,
                                    minHeight: 0,
                                    display: 'flex',
                                    flexDirection: 'column',
                                }}
                            />

                            <CustomerComparisonResultCard
                                title='比較月グループの顧客'
                                data={compareCustomers}
                                cardStyle={{
                                    backgroundColor: customTokens.colorBgBase,
                                }}
                                headStyle={{
                                    background:
                                        'linear-gradient(90deg, rgba(245,158,11,0.4), rgba(245,158,11,0.05))',
                                    color: '#333',
                                }}
                                style={{
                                    flex: 3,
                                    minHeight: 0,
                                    display: 'flex',
                                    flexDirection: 'column',
                                }}
                            />
                        </div>
                    )}
                </Col>
            </Row>
        </div>
    );
};

export default CustomerListAnalysis;
