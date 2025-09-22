import { isMobile as isMobileWidth } from '@/shared/constants/breakpoints';
import React, { useEffect, useRef, useState } from 'react';
import { Modal, Typography, Spin, Anchor, Row, Col } from 'antd';
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import manualsApi from '@/services/api/manualsApi';
import type { ManualSummary } from '@/types/manuals';
import type { ManualDetail } from '@/types/manuals';
import { ensureSectionAnchors, smoothScrollToAnchor } from '@/utils/anchors';

const { Title } = Typography;

const ManualModal: React.FC = () => {
  const { id } = useParams();
  const [data, setData] = useState<ManualDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [list, setList] = useState<ManualSummary[]>([]);
  const ref = useRef<HTMLDivElement>(null);
  const firstFocusable = useRef<HTMLHeadingElement>(null);
  const nav = useNavigate();
  const loc = useLocation();
  const [params] = useSearchParams();

  const isMobile = (typeof window !== 'undefined') && isMobileWidth(window.innerWidth);
  const forceFull = params.get('full') === '1';

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [d, l] = await Promise.all([
          manualsApi.get(id!),
          manualsApi.list({ category: 'syogun' }),
        ]);
        if (!alive) return;
        setData(d);
        setList(l.items);
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
    const hash = window.location.hash;
    if (hash) smoothScrollToAnchor(container, hash);
  }, [data]);

  // 直アクセス/モバイル/ ?full=1 は単独ページへリダイレクト
  useEffect(() => {
    if (forceFull || isMobile || !loc.state?.backgroundLocation) {
      // 単独ページにリプレース
      nav(`/manuals/syogun/${id}?full=1${window.location.hash || ''}`, { replace: true });
    }
  }, [forceFull, isMobile, loc.state, id, nav]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose();
        return;
      }
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        if (!id || list.length === 0) return;
        const idx = list.findIndex((x) => x.id === id);
        if (idx < 0) return;
        const nextIdx = e.key === 'ArrowLeft' ? idx - 1 : idx + 1;
        if (nextIdx < 0 || nextIdx >= list.length) return;
        const nextId = list[nextIdx].id;
        nav(`/manuals/syogun/${nextId}`, { state: { backgroundLocation: loc.state?.backgroundLocation || loc } });
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [id, list, nav, loc]);

  const handleClose = () => {
    if (loc.state?.backgroundLocation) {
      nav(-1);
    } else {
      nav('/manuals');
    }
  };

  return (
    <Modal open={!forceFull && !isMobile} onCancel={handleClose} onOk={handleClose} okText='閉じる' cancelButtonProps={{ style: { display: 'none' }}} title={data?.title || '読み込み中…'} width='80vw' centered styles={{ body: { height: '80vh', overflow: 'hidden', paddingTop: 8 }}} afterOpenChange={(open) => { if (open) firstFocusable.current?.focus(); }}>
      {loading ? <Spin /> : (
        <div style={{ height: '100%' }}>
          <Row gutter={[16, 16]} style={{ height: '100%' }}>
            <Col xs={24} md={6} style={{ height: '100%', overflow: 'auto' }}>
              <Anchor
                targetOffset={16}
                getContainer={() => ref.current as HTMLElement}
                items={data?.sections.map((s) => ({ key: s.anchor, href: `#${s.anchor}`, title: s.title }))}
                onClick={(e, link) => {
                  e.preventDefault();
                  if (!ref.current) return;
                  smoothScrollToAnchor(ref.current, link.href.replace(/^.*#/, '#'));
                }}
              />
            </Col>
            <Col xs={24} md={18}>
              <div ref={ref} style={{ height: '100%', overflow: 'auto' }}>
                <Title level={5} tabIndex={-1} ref={firstFocusable}>概要</Title>
                {data?.sections?.map((s) => (
                  <div key={s.anchor} dangerouslySetInnerHTML={{ __html: s.html || '' }} />
                ))}
              </div>
            </Col>
          </Row>
        </div>
      )}
    </Modal>
  );
};

export default ManualModal;
