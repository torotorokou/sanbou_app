// ChatQuestionSection.tsx
import React from 'react';
import { useWindowSize } from '@/hooks/ui';
import { BREAKPOINTS as BP } from '@/shared/constants/breakpoints';
import QuestionPanel from '@/components/chat/QuestionPanel';

type Props = {
    category: string;
    setCategory: (val: string) => void;
    tags: string[];
    setTag: (val: string[]) => void;
    template: string;
    setTemplate: (val: string) => void;
    question: string;
    setQuestion: (val: string) => void;
    // 関連PDFカードは削除済み
    // YAMLからのデータ
    categoryData?: Record<string, { title: string; tag: string[] }[]>;
};

// スタイルは親から渡すcardStyleを優先

const ChatQuestionSection: React.FC<Props> = ({
    category,
    setCategory,
    tags,
    setTag,
    template,
    setTemplate,
    question,
    setQuestion,
    categoryData,
}) => {
    const { width } = useWindowSize();
    const isNarrow = typeof width === 'number' ? width <= BP.mdMax : false;

    return (
        <div
            style={{
                width: isNarrow ? '100%' : 420,
                padding: 24,
                paddingBottom: isNarrow ? 8 : 88,
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
                minHeight: 0,
            }}
        >
            {/* QuestionPanelをそのまま使う */}
            <QuestionPanel
                category={category}
                setCategory={setCategory}
                tags={tags}
                setTag={setTag}
                template={template}
                setTemplate={setTemplate}
                question={question}
                setQuestion={setQuestion}
                categoryData={categoryData}
            />
        </div>
    );
};

export default ChatQuestionSection;
