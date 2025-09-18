import React, { useEffect, useState } from 'react';
import { Input, List, Space, Tag, Typography } from 'antd';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import manualsApi from '@/services/api/manualsApi';
import type { ManualSummary } from '@/types/manuals';

const { Title, Paragraph } = Typography;

const GlobalManualSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [items, setItems] = useState<ManualSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const nav = useNavigate();
  const loc = useLocation();

  useEffect(() => {
    const t = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await manualsApi.list({ query });
        setItems(res.items);
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(t);
  }, [query]);

  const openModal = (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    nav(`/manuals/syogun/${id}`, { state: { backgroundLocation: loc } });
  };

  return (
    <Space direction='vertical' size={16} style={{ width: '100%' }}>
      <Title level={3}>マニュアル全体検索</Title>
      <Paragraph type='secondary'>タイトル/説明/タグで横断検索。クリックでモーダル、直URLは単独ページ。</Paragraph>
      <Input.Search allowClear placeholder='キーワードで検索…（例：E票、見積、台帳）' value={query} onChange={(e) => setQuery(e.target.value)} />
      <List
        loading={loading}
        dataSource={items}
        renderItem={(it) => (
          <List.Item key={it.id} actions={[<Link key={`open-${it.id}`} to={`/manuals/syogun/${it.id}`} onClick={(e) => openModal(it.id, e)}>開く</Link>] }>
            <List.Item.Meta title={<Link to={`/manuals/syogun/${it.id}`} onClick={(e) => openModal(it.id, e)}>{it.title}</Link>} description={it.description} />
            <Space size={[4,4]} wrap>
              {(it.tags||[]).map((t) => <Tag key={t}>{t}</Tag>)}
            </Space>
          </List.Item>
        )}
      />
    </Space>
  );
};

export default GlobalManualSearch;
