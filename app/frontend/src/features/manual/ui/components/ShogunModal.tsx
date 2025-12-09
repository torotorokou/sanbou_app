/**
 * ManualModal UI Component
 * マニュアル詳細モーダル(純粋UI)
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Col, Flex, Modal, Row, Typography } from 'antd';
import type { ManualItem } from '../../domain/types/shogun.types';
import { FlowPane } from './FlowPane';
import { VideoPane, type VideoPaneRef } from './VideoPane';

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
  const videoPaneRef = React.useRef<VideoPaneRef>(null);

  const handleClose = () => {
    videoPaneRef.current?.stopVideo();
    onClose();
  };
  return (
    <Modal
      open={open}
      onCancel={handleClose}
      onOk={handleClose}
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
                  ref={videoPaneRef}
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
              disabled={!item.id && !item.route}
              onClick={() => {
                handleClose();
                // routeプロパティがある場合はそれを使用、なければ従来のパターン
                if (item.route) {
                  navigate(item.route);
                } else if (item.id) {
                  navigate(`/manuals/shogun/${item.id}`);
                } else {
                  console.warn('ManualModal: Cannot navigate - item.id and item.route are missing', item);
                }
              }}
            >
              詳細ページを開く
            </Button>
          </Flex>
        )}
      </div>
    </Modal>
  );
};
