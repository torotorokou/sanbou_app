import React from 'react';
import { Card, Typography } from 'antd';

type Props = {
    answer: string;
};

const AnswerViewer: React.FC<Props> = ({ answer }) => {
    return (
        <Card className='no-hover' style={{ height: '90%', overflowY: 'auto' }}>
            <Typography.Paragraph style={{ marginBottom: 0, color: '#333' }}>
                {answer
                    ? answer.split('\n').map((line, i) => (
                          <React.Fragment key={i}>
                              {line}
                              <br />
                          </React.Fragment>
                      ))
                    : 'ここに回答が表示されます'}
            </Typography.Paragraph>
        </Card>
    );
};

export default AnswerViewer;
