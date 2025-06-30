// src/components/ui/Sparkline.tsx
import React from 'react';
import { AreaChart, Area, ResponsiveContainer, Tooltip } from 'recharts';

type Props = {
    data: number[];
    height?: number;
    width?: number;
    strokeColor?: string;
    fillColor?: string;
};

const Sparkline: React.FC<Props> = ({
    data,
    height = 80,
    width = 120,
    strokeColor = '#722ED1',
    fillColor = '#722ED1',
}) => {
    const chartData = data.map((v, i) => ({ x: i, y: v }));

    return (
        <ResponsiveContainer width={width} height={height}>
            <AreaChart data={chartData}>
                <defs>
                    <linearGradient
                        id="sparklineGradient"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                    >
                        <stop
                            offset="0%"
                            stopColor={fillColor}
                            stopOpacity={0.3}
                        />
                        <stop
                            offset="100%"
                            stopColor={fillColor}
                            stopOpacity={0}
                        />
                    </linearGradient>
                </defs>
                <Tooltip />
                <Area
                    type="monotone"
                    dataKey="y"
                    stroke={strokeColor}
                    strokeWidth={2}
                    fill="url(#sparklineGradient)"
                    dot={false}
                />
            </AreaChart>
        </ResponsiveContainer>
    );
};

export default Sparkline;
