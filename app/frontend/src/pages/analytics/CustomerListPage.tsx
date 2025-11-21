/**
 * Customer List Analysis Page
 * 
 * FSD + MVVM + Repository パターンに準拠
 * 
 * Page層の責務:
 * - レイアウト/ルーティング/配置（骨組み）のみ
 * - ViewModel（useCustomerChurnViewModel）を呼び出し
 * - 純粋なUIコンポーネントにデータを流し込むだけ
 * - ビジネスロジック・状態管理・イベントハンドラは一切書かない
 */

import React from 'react';
import { Row, Col, Button, Card } from 'antd';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import { customTokens, apiPostBlob } from '@/shared';
import {
  PeriodSelectorForm,
  CustomerComparisonResultCard,
  AnalysisProcessingModal,
  useCustomerChurnViewModel,
} from '@features/analytics/customer-list';

const CustomerListAnalysis: React.FC = () => {
    // ViewModel を呼び出し（すべての状態・ロジック・イベントハンドラがここに集約）
    const vm = useCustomerChurnViewModel(apiPostBlob);

    return (
        <div style={{ height: '100%', minHeight: 0 }}>
            {/* 分析中モーダル */}
            <AnalysisProcessingModal open={vm.isAnalyzing} />

            <Row gutter={24} style={{ height: '100%', minHeight: 0 }}>
                {/* 左カラム: 条件指定・実行ボタン */}
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
                            title='条件指定'
                            variant="borderless"
                            style={{
                                boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
                                marginBottom: 24,
                                borderRadius: 16,
                            }}
                            styles={{
                                header: {
                                    background: '#f0f5ff',
                                    fontWeight: 600,
                                    borderTopLeftRadius: 16,
                                    borderTopRightRadius: 16,
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                },
                            }}
                            extra={
                                <Button
                                    type='primary'
                                    danger
                                    onClick={vm.resetConditions}
                                    size='middle'
                                    icon={<ReloadOutlined />}
                                    style={{ fontWeight: 600 }}
                                >
                                    リセット
                                </Button>
                            }
                        >
                            <PeriodSelectorForm
                                currentStart={vm.currentStart}
                                currentEnd={vm.currentEnd}
                                previousStart={vm.previousStart}
                                previousEnd={vm.previousEnd}
                                setCurrentStart={vm.setCurrentStart}
                                setCurrentEnd={vm.setCurrentEnd}
                                setPreviousStart={vm.setPreviousStart}
                                setPreviousEnd={vm.setPreviousEnd}
                            />
                        </Card>
                        
                        <Button
                            type='primary'
                            size='large'
                            block
                            disabled={vm.isButtonDisabled}
                            onClick={vm.handleAnalyze}
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
                            disabled={!vm.analysisStarted}
                            onClick={vm.handleDownloadLostCustomersCsv}
                            icon={<DownloadOutlined />}
                            style={{
                                fontWeight: 600,
                                letterSpacing: 1,
                                height: 48,
                                borderColor: '#f43f5e',
                                color: vm.analysisStarted ? '#f43f5e' : undefined,
                            }}
                        >
                            CSVダウンロード
                        </Button>
                    </div>
                </Col>

                {/* 右カラム: 分析結果表示 */}
                <Col
                    span={17}
                    style={{
                        height: '95%',
                        minHeight: 0,
                        display: 'flex',
                        flexDirection: 'column',
                    }}
                >
                    {!vm.analysisStarted ? (
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
                                title={`来なくなった顧客（離脱）: ${vm.lostCustomers.length} 件`}
                                data={vm.lostCustomers}
                                cardStyle={{
                                    backgroundColor:
                                        customTokens.colorBgContainer,
                                }}
                                headerStyle={{
                                    background:
                                        'linear-gradient(90deg, rgba(244,63,94,0.4), rgba(244,63,94,0.05))',
                                    color: '#333',
                                }}
                                style={{
                                    flex: 1,
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
