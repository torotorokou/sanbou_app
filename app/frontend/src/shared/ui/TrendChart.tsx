import React from 'react';
import {
    AreaChart,
    Area,
    ResponsiveContainer,
    Tooltip,
    YAxis,
    XAxis,
} from 'recharts';

type Props = {
    data: number[];
    height?: number;
    strokeColor?: string;
    fillColor?: string;
    minY?: number;
    maxY?: number;
};

// ✅ カスタムツールチップ
interface TrendPoint { x: number; y: number; total: number }
interface TooltipEntry { payload?: TrendPoint }
const CustomTooltip = ({
    active,
    payload,
}: {
    active?: boolean;
    payload?: TooltipEntry[];
}) => {
    if (active && payload && payload.length > 0) {
    const index = payload[0]?.payload?.x ?? 0;
    const value = payload[0]?.payload?.y ?? 0;
    const total = payload[0]?.payload?.total ?? 0;
    const dayDiff = total - index - 1;
        const labelText = dayDiff === 0 ? '今日' : `${dayDiff}日前`;

        return (
            <div
                style={{
                    background: '#fff',
                    border: '1px solid #ccc',
                    padding: 6,
                }}
            >
                <div>
                    <strong>{labelText}</strong>
                </div>
                <div>{value.toLocaleString()} 件</div>
            </div>
        );
    }
    return null;
};

const TrendChart: React.FC<Props> = ({
    data,
    height = 80,
    strokeColor = '#40a9ff',
    fillColor = '#40a9ff',
    minY,
    maxY,
}) => {
    const chartData = data.map((v, i) => ({
        x: i,
        y: v,
        total: data.length,
    }));

    return (
        <ResponsiveContainer width='100%' height={height}>
            <AreaChart data={chartData}>
                <defs>
                    <linearGradient
                        id='sparklineGradient'
                        x1='0'
                        y1='0'
                        x2='0'
                        y2='1'
                    >
                        <stop
                            offset='0%'
                            stopColor={fillColor}
                            stopOpacity={0.3}
                        />
                        <stop
                            offset='100%'
                            stopColor={fillColor}
                            stopOpacity={0}
                        />
                    </linearGradient>
                </defs>

                <YAxis
                    hide
                    domain={[minY ?? 'dataMin - 500', maxY ?? 'dataMax + 500']}
                />

                <XAxis
                    dataKey='x'
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10 }}
                    tickFormatter={(x) => {
                        const dayDiff = chartData.length - x - 1;
                        return dayDiff === 0 ? '今日' : `${dayDiff}日前`;
                    }}
                />

                <Tooltip content={<CustomTooltip />} />

                <Area
                    type='monotone'
                    dataKey='y'
                    stroke={strokeColor}
                    strokeWidth={2}
                    fill='url(#sparklineGradient)'
                    dot={false}
                />
            </AreaChart>
        </ResponsiveContainer>
    );
};

export default TrendChart;
