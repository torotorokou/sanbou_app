/**
 * 将軍マニュアル詳細ページ
 * FSD: ページ層は組み立てのみ
 */
import React, { useEffect, useRef, useState } from 'react';
import { Anchor, Breadcrumb, Button, Layout, Space, Spin, Typography } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import { manualsApiDefault as manualsApi, type ManualDetail, type ManualSectionChunk } from '@features/manual';
import { ensureSectionAnchors, smoothScrollToAnchor } from '@shared/utils/anchors';
import { useWindowSize } from '@shared/hooks/ui';
import { ANT } from '@/shared/constants/breakpoints';
import styles from './ShogunPage.module.css';

const { Title } = Typography;

const ShogunManualDetailPage: React.FC = () => {
  const { id } = useParams();
  const [data, setData] = useState<ManualDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const ref = useRef<HTMLDivElement>(null);
  const nav = useNavigate();
  const { width } = useWindowSize();
  const showSider = typeof width === 'number' ? width >= ANT.md : false;

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const d = await manualsApi.get(id!);
        if (!alive) return;
        setData(d);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [id]);

  useEffect(() => {
    const container = ref.current;
    if (!container) return;
    ensureSectionAnchors(container);
    if (window.location.hash) smoothScrollToAnchor(container, window.location.hash);
  }, [data]);

  return (
    <Layout className={styles.detailLayout}>
      {showSider && (
        <Layout.Sider width={240} className={styles.sider}>
          <div className={styles.siderContent}>
            <Anchor
              targetOffset={16}
              getContainer={() => document.querySelector('#manual-content-scroll') as HTMLElement || window}
              items={data?.sections.map((s: ManualSectionChunk) => ({ key: s.anchor, href: `#${s.anchor}`, title: s.title }))}
            />
          </div>
        </Layout.Sider>
      )}

      <Layout.Content className={styles.content}>
        <Space direction='vertical' size={12} style={{ width: '100%' }}>
          <Breadcrumb items={[{ title: 'マニュアル' }, { title: '将軍' }, { title: data?.title || '' }]} />
          <div className={styles.titleBar}>
            <Title level={3} className={styles.title}>{data?.title}</Title>
            <Button onClick={() => nav(`/manuals/syogun/${id}`, { state: { backgroundLocation: { pathname: '/manuals' } } })}>
              モーダルで開く
            </Button>
          </div>
        </Space>
        <div id='manual-content-scroll' className={styles.scrollContainer}>
          {loading ? (
            <div className={styles.loadingContainer}><Spin size='large' /></div>
          ) : (
            <div ref={ref}>
              {data?.sections.map((section: ManualSectionChunk) => (
                <section key={section.anchor} id={section.anchor}>
                  <h2>{section.title}</h2>
                  <div dangerouslySetInnerHTML={{ __html: section.html || '' }} />
                </section>
              ))}
            </div>
          )}
        </div>
      </Layout.Content>
    </Layout>
  );
};

export default ShogunManualDetailPage;
