/**
 * 将軍マニュアル詳細コンテンツ表示 UI
 * - 純粋な表示コンポーネント（状態を持たない）
 */
import React from 'react';
import type { ManualSectionChunk } from '../../domain/types/shogun.types';

export interface DetailContentProps {
  sections: ManualSectionChunk[];
}

export const DetailContent: React.FC<DetailContentProps> = ({ sections }) => {
  return (
    <div>
      {sections.map((section) => (
        <section key={section.anchor} id={section.anchor}>
          <h2>{section.title}</h2>
          <div dangerouslySetInnerHTML={{ __html: section.html || '' }} />
        </section>
      ))}
    </div>
  );
};
