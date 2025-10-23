// features/navi/hooks/useNaviChat.ts
// ViewModel (状態管理・副作用・リポジトリ呼び出し)

import { useEffect, useMemo, useState } from 'react';
import { NaviRepositoryImpl } from '../infrastructure/navi.repository';
import type { CategoryDataMap } from '../domain/types/types';
import { useNotificationStore } from '@features/notification';

/**
 * Naviチャット機能のViewModel Hook
 */
export function useNaviChat() {
  // Repository インスタンス（useMemoで再生成を防ぐ）
  const repo = useMemo(() => new NaviRepositoryImpl(), []);

  // 通知ストアから追加関数を取得
  const addNotification = useNotificationStore((s) => s.addNotification);

  // 状態管理
  const [category, setCategory] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [template, setTemplate] = useState('自由入力');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfToShow, setPdfToShow] = useState<string | null>(null);
  const [pdfModalVisible, setPdfModalVisible] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  // カテゴリデータ（質問テンプレート）
  const [categoryData, setCategoryData] = useState<CategoryDataMap>({});

  // 初回マウント時に質問テンプレート一覧を取得
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const data = await repo.getQuestionOptions();
        setCategoryData(data);
      } catch (err) {
        console.error('[API][ERROR] /question-options:', err);
        setCategoryData({});
        addNotification({
          type: 'error',
          title: '質問テンプレートの取得に失敗',
          message: 'カテゴリ・テンプレート候補を取得できませんでした。',
          duration: 4000,
        });
      }
    };
    fetchOptions();
  }, [repo, addNotification]);

  // タグの一意化・空除去（送信用）
  const tagsToSend = useMemo(
    () => Array.from(new Set(tags)).filter(Boolean),
    [tags]
  );

  // タグは最大3件までに制限するハンドラ
  const handleSetTag = (val: string[] | ((prev: string[]) => string[])) => {
    let nextTags: string[] = [];
    if (typeof val === 'function') {
      try {
        nextTags = val(tags) || [];
      } catch {
        nextTags = tags;
      }
    } else {
      nextTags = val || [];
    }
    // 一意化・空文字除去
    nextTags = Array.from(new Set(nextTags)).filter(Boolean);
    if (nextTags.length > 3) {
      addNotification({
        type: 'warning',
        title: 'タグは3つまでです',
        message: 'タグは最大3つまで選択できます。先に選択した3つが採用されます。',
        duration: 3000,
      });
      nextTags = nextTags.slice(0, 3);
    }
    setTags(nextTags);
  };

  // AI回答を取得
  const handleSearch = async (): Promise<void> => {
    if (!question.trim()) return;
    setCurrentStep(3);
    setLoading(true);

    const payload = {
      query: question,
      category: category,
      tags: tagsToSend,
    };

    console.log('[API][REQUEST] /rag_api/api/generate-answer payload:', payload);

    try {
      const result = await repo.generateAnswer(payload);

      console.log('[API][RESPONSE] data:', result);

      setAnswer(result.answer);
      setPdfUrl(result.pdfUrl ?? null);

      addNotification({
        type: 'success',
        title: 'AI応答を取得しました',
        message: result.pdfUrl
          ? '回答とPDFリンクを受信しました。'
          : '回答を受信しました。',
        duration: 2500,
      });
    } catch (err: unknown) {
      console.error('[API][ERROR]', err);
      setAnswer('エラーが発生しました。');
      setPdfUrl(null);

      addNotification({
        type: 'error',
        title: '取得に失敗しました',
        message: 'ネットワークまたはサーバーエラーです。',
        duration: 4000,
      });
    } finally {
      setLoading(false);
    }
  };

  return {
    // 状態
    category,
    tags,
    template,
    question,
    answer,
    loading,
    pdfUrl,
    pdfToShow,
    pdfModalVisible,
    currentStep,
    categoryData,
    tagsToSend,

    // セッター
    setCategory,
    setTags: handleSetTag,
    setTemplate,
    setQuestion,
    setPdfToShow,
    setPdfModalVisible,
    setCurrentStep,

    // アクション
    handleSearch,
  };
}
