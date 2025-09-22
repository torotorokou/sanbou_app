import React, { useEffect, useRef, useState } from 'react';
import { Anchor, Breadcrumb, Button, Layout, Space, Spin, Typography } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import manualsApi from '@/services/api/manualsApi';
import type { ManualDetail } from '@/types/manuals';
import { ensureSectionAnchors, smoothScrollToAnchor } from '@/utils/anchors';
import { useWindowSize } from '@/hooks/ui';
import { BREAKPOINTS as BP } from '@/shared/constants/breakpoints';

const { Title } = Typography;

const ManualPage: React.FC = () => {
  const { id } = useParams();
  const [data, setData] = useState<ManualDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const ref = useRef<HTMLDivElement>(null);
  const nav = useNavigate();
  const { width } = useWindowSize();
  const showSider = typeof width === 'number' ? width >= BP.sm + 1 : false; // md以上で表示

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
    <Layout style={{ height: '100%', background: 'transparent' }}>
      {showSider && (
        <Layout.Sider width={240} style={{ position: 'sticky', top: 0, alignSelf: 'flex-start', height: '100vh', overflow: 'auto', background: 'var(--ant-color-bg-container, #fff)', borderRight: '1px solid var(--ant-color-border-secondary, #f0f0f0)' }}>
          <div style={{ padding: 16 }}>
            <Anchor
              targetOffset={16}
              getContainer={() => document.querySelector('#manual-content-scroll') as HTMLElement || window}
              items={data?.sections.map((s) => ({ key: s.anchor, href: `#${s.anchor}`, title: s.title }))}
            />
          </div>
        </Layout.Sider>
      )}

      <Layout.Content style={{ padding: 16 }}>
        <Space direction='vertical' size={12} style={{ width: '100%' }}>
          <Breadcrumb items={[{ title: 'マニュアル' }, { title: '将軍' }, { title: data?.title || '' }]} />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={3} style={{ margin: 0 }}>{data?.title}</Title>
            <Button onClick={() => nav(`/manuals/syogun/${id}`, { state: { backgroundLocation: { pathname: '/manuals' } } })}>モーダルで開く</Button>
          </div>
          {loading ? <Spin /> : (
            <div id="manual-content-scroll" ref={ref} style={{ maxHeight: 'calc(100vh - 160px)', overflowY: 'auto', paddingRight: 8 }}>
              {data?.sections.map((s) => (
                <div key={s.anchor} style={{ scrollMarginTop: 80 }} dangerouslySetInnerHTML={{ __html: s.html || '' }} />
              ))}
            </div>
          )}
        </Space>
      </Layout.Content>
    </Layout>
  );
};

export default ManualPage;
