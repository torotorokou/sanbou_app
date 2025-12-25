/**
 * 業者マスターページ
 * FSD: ページ層は組み立てのみ
 */
import React from "react";
import { Breadcrumb, Col, Layout, Row, Space, Spin, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import { useShogunCatalog } from "@features/manual";
import { FlowPane } from "@features/manual/ui/components/FlowPane";
import { VideoPane } from "@features/manual/ui/components/VideoPane";
import styles from "./VendorMaster.module.css";

const { Title, Paragraph } = Typography;

const VendorMasterPage: React.FC = () => {
  const nav = useNavigate();

  // カタログから業者マスター情報を取得
  const { sections, loading } = useShogunCatalog();
  const vendorItem = React.useMemo(() => {
    const masterSection = sections.find((s) => s.id === "master");
    if (masterSection) {
      return masterSection.items.find((item) => item.id === "vendor");
    }
    return null;
  }, [sections]);

  return (
    <Layout className={styles.detailLayout}>
      <Layout.Content className={styles.detailContent}>
        <Space
          direction="vertical"
          size={12}
          style={{ width: "100%", marginBottom: 16 }}
        >
          <Breadcrumb
            items={[
              {
                title: (
                  <a
                    onClick={() => nav("/manuals")}
                    className={styles.detailLink}
                  >
                    マニュアル
                  </a>
                ),
              },
              {
                title: (
                  <a
                    onClick={() => nav("/manuals/shogun")}
                    className={styles.detailLink}
                  >
                    将軍
                  </a>
                ),
              },
              { title: "マスター情報" },
              { title: "業者" },
            ]}
          />
          <div className={styles.detailTitleBar}>
            <Title level={3} className={styles.detailTitle}>
              {vendorItem?.title || "業者マスター"}
            </Title>
          </div>
        </Space>

        {loading ? (
          <div className={styles.detailLoadingContainer}>
            <Spin size="large" />
          </div>
        ) : !vendorItem ? (
          <div style={{ padding: 24, textAlign: "center" }}>
            <Typography.Text type="secondary">
              マニュアルが見つかりません
            </Typography.Text>
          </div>
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 16,
              padding: 16,
            }}
          >
            {/* 概要 */}
            <div
              style={{
                maxHeight: "20vh",
                overflow: "auto",
                padding: 16,
                background: "#fafafa",
                borderRadius: 8,
              }}
            >
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                {vendorItem.description ??
                  "運搬業者・処分業者の管理に関するマニュアルです。"}
              </Paragraph>
            </div>

            {/* フロー・動画 */}
            <Row gutter={[16, 16]}>
              <Col xs={24} md={7}>
                <Title level={5} style={{ marginTop: 0 }}>
                  フローチャート
                </Title>
                <div className={styles.flowPane}>
                  <FlowPane
                    src={vendorItem.flowUrl}
                    title={vendorItem.title ?? "業者マスターフロー"}
                    frameClassName={styles.paneFrame}
                    imgClassName={styles.paneImg}
                  />
                </div>
              </Col>

              <Col xs={24} md={17}>
                <Title level={5} style={{ marginTop: 0 }}>
                  動画
                </Title>
                <div className={styles.videoPane}>
                  <VideoPane
                    src={vendorItem.videoUrl}
                    title={vendorItem.title ?? "業者マスター動画"}
                    frameClassName={styles.paneFrame}
                    videoClassName={styles.paneFrame}
                  />
                </div>
              </Col>
            </Row>
          </div>
        )}
      </Layout.Content>
    </Layout>
  );
};

export default VendorMasterPage;
