import React, { useEffect, useRef, useState } from 'react';
import { Anchor, Breadcrumb, Button, Grid, Space, Spin, Typography } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import manualsApi from '@/services/api/manualsApi';
import type { ManualDetail } from '@/types/manuals';
import { ensureSectionAnchors, smoothScrollToAnchor } from '@/utils/anchors';

const { Title } = Typography;
const { useBreakpoint } = Grid;

const ManualPage: React.FC = () => {
  const { id } = useParams();
  const [data, setData] = useState<ManualDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const ref = useRef<HTMLDivElement>(null);
  const nav = useNavigate();
  const screens = useBreakpoint();

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
    <div style={{ display: 'grid', gridTemplateColumns: screens.lg ? '240px 1fr' : '1fr', gap: 16 }}>
      {screens.lg && (
        <div>
          <Anchor
            targetOffset={16}
            items={data?.sections.map((s) => ({ key: s.anchor, href: `#${s.anchor}`, title: s.title }))}
          />
        </div>
      )}

      <div>
        <Space direction='vertical' size={12} style={{ width: '100%' }}>
          <Breadcrumb items={[{ title: 'マニュアル' }, { title: '将軍' }, { title: data?.title || '' }]} />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={3} style={{ margin: 0 }}>{data?.title}</Title>
            <Button onClick={() => nav(`/manuals/syogun/${id}`, { state: { backgroundLocation: { pathname: '/manuals' } } })}>モーダルで開く</Button>
          </div>
          {loading ? <Spin /> : (
            <div ref={ref}>
              {data?.sections.map((s) => (
                <div key={s.anchor} dangerouslySetInnerHTML={{ __html: s.html || '' }} />
              ))}
            </div>
          )}
        </Space>
      </div>
    </div>
  );
};

export default ManualPage;
