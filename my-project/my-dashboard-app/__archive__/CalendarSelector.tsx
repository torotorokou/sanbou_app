import React from 'react';
import { Card, Calendar } from 'antd';
import type { CalendarProps } from 'antd';
import { Dayjs } from 'dayjs';
import { customTokens } from '@/theme/tokens';

type CalendarSelectorProps = {
    selectedDate: Dayjs | null;
    onSelect: CalendarProps<Dayjs>['onSelect'];
};

const CalendarSelector: React.FC<CalendarSelectorProps> = ({
    selectedDate,
    onSelect,
}) => {
    return (
        <Card
            size='small'
            styles={{ body: { padding: 8 } }} // ✅ 正しい書き方
            style={{ backgroundColor: customTokens.colorBgLayout }}
        >
            <Calendar
                fullscreen={false}
                value={selectedDate || undefined}
                onSelect={onSelect}
            />
        </Card>
    );
};

export default CalendarSelector;
