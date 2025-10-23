/**
 * ManualModal UI Component
 * マニュアル詳細モーダル（純粋UI）
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Col, Flex, Modal, Row, Typography } from 'antd';
import type { ManualItem } from '../../domain/types/shogun.types';
import { FlowPane } from './FlowPane';
import { VideoPane } from './VideoPane';

const { Title, Paragraph } = Typography;

export interface ManualModalProps {
  open: boolean;
  item: ManualItem | null;
  onClose: () => void;
  flowPaneClassName?: string;
  videoPaneClassName?: string;
  paneFrameClassName?: string;
  paneImgClassName?: string;
  paneVideoClassName?: string;
}

export const ManualModal: React.FC<ManualModalProps> = ({
  open,
  item,
  onClose,
  flowPaneClassName,
  videoPaneClassName,
  paneFrameClassName,
  paneImgClassName,
  paneVideoClassName,
}) => {
  const navigate = useNavigate();
  return (
    <Modal
      open={open}
      onCancel={onClose}
      onOk={onClose}
      okText="閉じる"
      cancelButtonProps={{ style: { display: 'none' } }}
      title={item?.title ?? 'マニュアル'}
      width="80vw"
      centered
      styles={{
        body: { height: '80vh', overflow: 'hidden', paddingTop: 8 },
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 12 }}>
        <div style={{ maxHeight: '20vh', overflow: 'auto' }}>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {item?.description ?? '説明は未設定です。'}
          </Paragraph>
        </div>

        <div style={{ flex: 1, minHeight: 0 }}>
          <Row gutter={[16, 16]} style={{ height: '100%' }}>
            <Col xs={24} md={7} style={{ height: '100%' }}>
              <Title level={5} style={{ marginTop: 0 }}>
                フローチャート
              </Title>
              <div className={flowPaneClassName}>
                <FlowPane
                  src={item?.flowUrl}
                  title={item?.title ?? 'flow'}
                  frameClassName={paneFrameClassName}
                  imgClassName={paneImgClassName}
                />
              </div>
            </Col>

            <Col xs={24} md={17} style={{ height: '100%' }}>
              <Title level={5} style={{ marginTop: 0 }}>
                動画
              </Title>
              <div className={videoPaneClassName}>
                <VideoPane
                  src={item?.videoUrl}
                  title={item?.title ?? 'video'}
                  frameClassName={paneFrameClassName}
                  videoClassName={paneVideoClassName}
                />
              </div>
            </Col>
          </Row>
        </div>

        {item && (
          <Flex justify="end">
            <Button
              type="link"
              disabled={!item.id}
              onClick={() => {
                // Guard: Ensure item.id exists before navigating
                if (!item.id) {
                  console.warn('ManualModal: Cannot navigate - item.id is missing', item);
                  return;
                }
                onClose();
                // Use backend-provided id for routing to ensure we open the canonical DetailPage.
                // Ignore item.route here to avoid slug/relative-path mismatches.
                navigate(`/manuals/syogun/${item.id}`);
              }}
            >
              関連ページを開く
            </Button>
          </Flex>
        )}
      </div>
    </Modal>
  );
};
