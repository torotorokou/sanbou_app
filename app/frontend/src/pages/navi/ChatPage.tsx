import React from 'react';
import { useNaviChat } from '@features/navi/hooks/useNaviChat';
import { NaviLayout } from '@features/navi/ui';
import { PdfReferenceButton } from '@features/navi/ui';
import { normalizePdfUrl } from '@features/navi/utils/pdfUrlNormalizer';
import type { StepItem } from '@features/navi/model/types';
import styles from './ChatPage.module.css';

const stepItems: StepItem[] = [
  { title: '分類', description: 'カテゴリ選択' },
  { title: '質問作成', description: '質問入力' },
  { title: '送信', description: 'AIに質問' },
  { title: '結果', description: '回答を確認' },
];

const ChatPage: React.FC = () => {
  const vm = useNaviChat();

  const handlePdfClick = () => {
    if (vm.pdfUrl) {
      const url = normalizePdfUrl(vm.pdfUrl);
      console.log('[参考PDF URL]', url);
      vm.setPdfToShow(url);
      vm.setPdfModalVisible(true);
    }
  };

  return (
    <div className={styles.pageContainer}>
      <NaviLayout
        loading={vm.loading}
        currentStep={vm.currentStep}
        category={vm.category}
        tags={vm.tags}
        template={vm.template}
        question={vm.question}
        answer={vm.answer}
        categoryData={vm.categoryData}
        pdfModalVisible={vm.pdfModalVisible}
        pdfToShow={vm.pdfToShow}
        setCategory={vm.setCategory}
        setTags={vm.setTags}
        setTemplate={vm.setTemplate}
        setQuestion={vm.setQuestion}
        setCurrentStep={vm.setCurrentStep}
        setPdfModalVisible={vm.setPdfModalVisible}
        setPdfToShow={vm.setPdfToShow}
        handleSearch={vm.handleSearch}
        stepItems={stepItems}
      />

      <PdfReferenceButton pdfUrl={vm.pdfUrl} onClick={handlePdfClick} />
    </div>
  );
};

export default ChatPage;
