import React, { useEffect, useMemo } from 'react';
import { Card, Select, Input, Typography, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import './QuestionPanel.css';

const { Option } = Select;
const { TextArea } = Input;

type Props = {
    category: string;
    setCategory: (val: string) => void;
    tags: string[];
    setTag: (val: string[]) => void;
    template: string;
    setTemplate: (val: string) => void;
    question: string;
    setQuestion: (val: string) => void;
    // YAMLからのデータ（カテゴリ: [{ title, tag: string[] }]）
    categoryData?: Record<string, { title: string; tag: string[] }[]>;
};

const QuestionPanel: React.FC<Props> = ({
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
    // 選択肢をYAMLから動的生成
    const categoryOptions = useMemo(
        () => (categoryData ? Object.keys(categoryData) : []),
        [categoryData]
    );
    // タグ候補は「カテゴリ配下の全テンプレートに付随するタグの集合」
    const tagOptions = useMemo(() => {
        if (!category || !categoryData) return [] as string[];
        const items = categoryData[category] || [];
        const all = new Set<string>();
        items.forEach((it) => (it.tag || []).forEach((t) => all.add(t)));
        return Array.from(all);
    }, [category, categoryData]);

    // テンプレート候補は「カテゴリ内のテンプレート」→
    // さらに選択タグがあれば、そのタグを1つ以上含むテンプレートに絞り込み
    const templateOptions = useMemo(() => {
        if (!category || !categoryData) return [] as string[];
        const items = categoryData[category] || [];
        if (!tags || tags.length === 0) return items.map((it) => it.title);
        return items
            .filter((it) => (it.tag || []).some((t) => tags.includes(t)))
            .map((it) => it.title);
    }, [category, tags, categoryData]);

    // 依存関係の変更により、カテゴリ/タグ変更で現在のテンプレートが不正になったらリセット
    useEffect(() => {
        if (template !== '自由入力' && !templateOptions.includes(template)) {
            setTemplate('自由入力');
        }
    }, [category, tags, templateOptions, template, setTemplate]);

    // カテゴリが変わったらタグを確実にリセット（親でも実施しているが二重防御）
    useEffect(() => {
        // 親からすでに空配列が来ている場合は何もしない
        if (!category && tags.length === 0) return;
        // カテゴリ変更でタグ候補が変わるため、選択済みタグは一旦クリア
        setTag([]);
        // ついでに質問文も空にする
        setQuestion('');
    }, [category]);

    // タグ候補(tagOptions)が変わった場合、候補に存在しないタグは除外して整合性を保つ
    useEffect(() => {
        if (!tags || tags.length === 0) return;
        const filtered = tags.filter((t) => tagOptions.includes(t));
        if (filtered.length !== tags.length) {
            setTag(filtered);
        }
    }, [tagOptions]);

    return (
        <div style={{ marginBottom: 16 /* ←狭く */ }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <Typography.Title level={4} style={{ margin: 0 }}>
                    質問を入力
                </Typography.Title>
                <Button
                    size='small'
                    type='text'
                    icon={<ReloadOutlined />}
                    onClick={() => {
                        setCategory('');
                        setTag([]);
                        setTemplate('自由入力');
                        setQuestion('');
                    }}
                    disabled={!category && tags.length === 0 && template === '自由入力' && !question}
                    title='カテゴリ・タグ・テンプレート・質問文をすべて初期化'
                >
                    すべてリセット
                </Button>
            </div>
            <Card
                bordered={false}
                className='no-hover'
                style={{
                    borderRadius: 16,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    padding: 16, // ←狭く
                    minHeight: 0, // ←または削除
                    display: 'flex',
                    flexDirection: 'column',
                }}
            >
                <div style={{ marginBottom: 14 }}>
                    <Typography.Text strong>カテゴリ</Typography.Text>
                    <Select
                        placeholder='カテゴリを選択'
                        value={category || undefined}
                        onChange={setCategory}
                        style={{ width: '100%', marginTop: 4 /* ←狭く */ }}
                    >
                        {categoryOptions.map((cat) => (
                            <Option key={cat} value={cat}>
                                {cat}
                            </Option>
                        ))}
                    </Select>
                </div>

                {/* 絞り順: カテゴリ → タグ（必須） → テンプレート */}
                <div style={{ marginBottom: 12 }}>
                    <Typography.Text strong>タグ（最大3つまで）</Typography.Text>
                    <Select
                        key={category || 'no-category'}
                        mode='multiple'
                        placeholder='タグを選択（必須）'
                        value={tags}
                        onChange={(vals) => setTag(Array.from(new Set(vals)))}
                        allowClear
                        style={{ width: '100%', marginTop: 4 }}
                        disabled={!category}
                        className='question-select question-select--tags'
                        listHeight={360}
                    >
                        {tagOptions.map((t) => (
                            <Option key={t} value={t}>
                                {t}
                            </Option>
                        ))}
                    </Select>
                </div>

                <div style={{ marginBottom: 18 }}>
                    <Typography.Text strong>質問テンプレート</Typography.Text>
                    <Select
                        value={template}
                        onChange={(val) => {
                            setTemplate(val);
                            if (val !== '自由入力') {
                                // setTemplate と競合してテンプレートがリセットされるケースを避けるため
                                // setQuestion は次のイベントループで実行する
                                setTimeout(() => setQuestion(val), 0);
                            }
                        }}
                        style={{ width: '100%', marginTop: 4 }}
                        disabled={!category || tags.length === 0}
                        popupClassName='template-select-dropdown'
                        className='template-select question-select question-select--template'
                        listHeight={360}
                    >
                        <Option value='自由入力'>
                            <div style={{ whiteSpace: 'normal', wordBreak: 'break-word', overflowWrap: 'anywhere', lineHeight: 1.4 }}>
                                自由入力
                            </div>
                        </Option>
                        {templateOptions.map((t) => (
                            <Option key={t} value={t}>
                                <div style={{ whiteSpace: 'normal', wordBreak: 'break-word', overflowWrap: 'anywhere', lineHeight: 1.4 }}>
                                    {t}
                                </div>
                            </Option>
                        ))}
                    </Select>
                </div>

                <div style={{ marginBottom: 0, marginTop: 35 }}>
                    <Typography.Text strong>質問内容</Typography.Text>
                    <TextArea
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder='質問を入力してください'
                        allowClear
                        // ↓ここを修正
                        autoSize={{ minRows: 8, maxRows: 14 }} // ←好きな行数で大きく
                        style={{
                            marginTop: 8,
                            minHeight: 160, // ←高さ指定（または不要なら消す）
                            fontSize: 16, // ←フォントもやや大きく（任意）
                        }}
                    />
                </div>
            </Card>
        </div>
    );
};

export default QuestionPanel;
