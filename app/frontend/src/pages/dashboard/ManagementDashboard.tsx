import React from 'react';
import { Typography } from 'antd';
import './ManagementDashboard.css';
import {
    SummaryPanel,
    CustomerAnalysis,
    RevenuePanel,
    BlockCountPanel,
    ProcessVolumePanel,
} from '@features/dashboard';

const { Title } = Typography;
const ManagementDashboard: React.FC = () => {
    return (
        <div className='dashboard-root'>
            <Title level={3} className='dashboard-title'>
                2025年6月27日 実績ダッシュボード
            </Title>

            <div className='dashboard-main'>
                {/* left column */}
                <div className='left-column'>
                    <div className='panel card-wrapper'>
                        <SummaryPanel />
                    </div>

                    <div className='panel card-wrapper'>
                        <RevenuePanel />
                    </div>
                </div>

                {/* right column */}
                <div className='right-column'>
                    <div className='panel-top card-wrapper'>
                        <CustomerAnalysis />
                    </div>

                    <div className='panel-mid card-wrapper'>
                        <ProcessVolumePanel />
                    </div>

                    <div className='panel-bottom card-wrapper'>
                        <BlockCountPanel />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ManagementDashboard;
