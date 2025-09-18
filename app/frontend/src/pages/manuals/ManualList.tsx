import React, { useEffect, useRef, useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Input, List, Space, Tag, Typography } from 'antd';
import manualsApi from '@/services/api/manualsApi';
import type { ManualSummary } from '@/types/manuals';
import { useManualsStore } from '@/stores/manualsStore';

const { Title, Paragraph } = Typography;

const ManualList: React.FC = () => {
  const [items, setItems] = useState<ManualSummary[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { listScrollY, setListScrollY } = useManualsStore();
  const nav = useNavigate();
  const loc = useLocation();

  const fetchList = async () => {
    setLoading(true);
    try {
      const data = await manualsApi.list({ category: 'syogun', query });
      setItems(data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchList();
    // 復元
    const y = listScrollY;
    if (ref.current && y > 0) {
      ref.current.scrollTo({ top: y });
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(fetchList, 250);
    return () => clearTimeout(t);
  }, [query]);

  const onOpen = (id: string, e: React.MouseEvent) => {
    setListScrollY(ref.current?.scrollTop || 0);
    nav(`/manuals/syogun/${id}`, { state: { backgroundLocation: loc } });
    e.preventDefault();
  };

  return (
    <div ref={ref} style={{ height: '100%', overflow: 'auto' }}>
      <Space direction='vertical' size={16} style={{ width: '100%' }}>
        <Title level={3}>将軍マニュアル一覧</Title>
        <Paragraph type='secondary'>一覧からクリックでモーダル、直アクセス/モバイル/ ?full=1 は単独表示。</Paragraph>
        <Input.Search allowClear placeholder='検索…' value={query} onChange={(e) => setQuery(e.target.value)} />
        <List
          loading={loading}
          dataSource={items}
          renderItem={(it) => (
            <List.Item key={it.id} actions={[<Link key={`open-${it.id}`} to={`/manuals/syogun/${it.id}`} onClick={(e) => onOpen(it.id, e)}>開く</Link>] }>
              <List.Item.Meta title={<Link to={`/manuals/syogun/${it.id}`} onClick={(e) => onOpen(it.id, e)}>{it.title}</Link>} description={it.description} />
              <Space size={[4,4]} wrap>
                {(it.tags||[]).map((t) => <Tag key={t}>{t}</Tag>)}
              </Space>
            </List.Item>
          )}
        />
      </Space>

      {/* モーダルルートをここでレンダリング */}
      <Outlet />
    </div>
  );
};

export default ManualList;
