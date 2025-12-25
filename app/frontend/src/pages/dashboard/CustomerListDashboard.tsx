import React, { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Circle,
  Tooltip,
  Marker,
  Popup,
  GeoJSON,
} from "react-leaflet";
import type { FeatureCollection } from "geojson";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Card, Table, Statistic, Row, Col } from "antd";
import type { ColumnsType } from "antd/es/table";
import { customerAnalysisColors } from "@shared/theme";

// 会社マーカー
const companyIcon = new L.Icon({
  iconUrl: "/marker-icon-red.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  shadowSize: [41, 41],
});

// カラースケール（色・閾値・ラベルを統一管理）
const colorScale = customerAnalysisColors;

// バブルの色取得関数（colorScaleと完全連動）
const getColor = (sales: number) => {
  for (const { threshold, color } of colorScale) {
    if (sales >= threshold) return color;
  }
  return colorScale[colorScale.length - 1].color;
};

type Customer = {
  id: number;
  name: string;
  lat: number;
  lng: number;
  sales: number;
};

const customers: Customer[] = Array.from({ length: 50 }, (_, i) => {
  const areas = [
    { pref: "東京", lat: 35.7, lng: 139.7 },
    { pref: "神奈川", lat: 35.4, lng: 139.6 },
    { pref: "埼玉", lat: 35.9, lng: 139.6 },
    { pref: "千葉", lat: 35.6, lng: 140.1 },
    { pref: "横浜", lat: 35.5, lng: 139.6 },
    { pref: "川崎", lat: 35.5, lng: 139.7 },
    { pref: "船橋", lat: 35.7, lng: 139.98 },
    { pref: "大宮", lat: 35.9, lng: 139.62 },
    { pref: "立川", lat: 35.7, lng: 139.41 },
    { pref: "町田", lat: 35.5, lng: 139.45 },
  ];
  const companies = [
    "商事",
    "産業",
    "エンタープライズ",
    "メタル",
    "トレーディング",
    "電材",
    "物流",
    "サービス",
    "工業",
    "リサイクル",
    "工務店",
    "企画",
    "建設",
    "技研",
    "ファクトリー",
  ];
  const area = areas[Math.floor(Math.random() * areas.length)];
  const comp = companies[Math.floor(Math.random() * companies.length)];
  const name = `${area.pref}${comp}${String.fromCharCode(65 + Math.floor(Math.random() * 26))}`;
  const lat = area.lat + (Math.random() - 0.5) * 0.1;
  const lng = area.lng + (Math.random() - 0.5) * 0.1;
  const sales = Math.floor(50 + Math.random() * 300);
  return {
    id: i + 1,
    name,
    lat: Math.round(lat * 10000) / 10000,
    lng: Math.round(lng * 10000) / 10000,
    sales,
  };
});

// バブル半径（売上大きいほど大きく）
const getRadius = (sales: number) => Math.sqrt(sales) * 400;

// ---- Table等は省略せず維持 ----
const sortedCustomers = [...customers].sort((a, b) => b.sales - a.sales);
const columns: ColumnsType<Customer> = [
  {
    title: "順位",
    key: "rank",
    render: (_value, _record, index: number) => index + 1,
    width: 60,
  },
  { title: "顧客名", dataIndex: "name", key: "name" },
  {
    title: "売上",
    dataIndex: "sales",
    key: "sales",
    render: (v: number) => `${v} 万円`,
  },
];
const totalSales = customers.reduce((sum, c) => sum + c.sales, 0);
const MAP_HEIGHT = 600;
const HQ_POSITION: [number, number] = [35.644975673671276, 139.83649644682137];

const GEOJSON_URL = "/prefectures.geojson";
const prefColorMap: Record<string, string> = {
  東京都: "#f88181ff",
  神奈川県: "#ffda74ff",
  埼玉県: "#11ff61ff",
  千葉県: "#bc9bffff",
};
function getPrefColor(name: string): string {
  return prefColorMap[name] || "#ffffff";
}
function getCenterOfGeometry(
  feature: FeatureCollection["features"][0],
): [number, number] {
  const { geometry } = feature;

  if (!("coordinates" in geometry)) {
    return [0, 0];
  }

  // MultiPolygon/Polygonのネストした座標配列を扱う
  let coords: unknown = geometry.coordinates;
  if (geometry.type === "MultiPolygon") {
    coords = (coords as number[][][][])[0][0];
  } else if (geometry.type === "Polygon") {
    coords = (coords as number[][][])[0];
  } else {
    return [0, 0];
  }

  let lat = 0,
    lng = 0,
    count = 0;
  (coords as number[][]).forEach((point: number[]) => {
    lat += point[1];
    lng += point[0];
    count++;
  });
  if (count === 0) return [0, 0];
  return [lat / count, lng / count];
}

const CustomerListDashboard: React.FC = () => {
  const [prefGeoJson, setPrefGeoJson] = useState<FeatureCollection | null>(
    null,
  );

  useEffect(() => {
    fetch(GEOJSON_URL)
      .then((res) => res.json())
      .then(setPrefGeoJson);
  }, []);

  return (
    <div
      style={{
        minHeight: "100%",
        display: "flex",
        flexDirection: "column",
        background: "#f7f8fa",
      }}
    >
      <div style={{ padding: 24 }}>
        <h1>一都三県 顧客売上バブルマップ</h1>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col xs={24} md={8}>
            <Statistic title="顧客数" value={customers.length} />
          </Col>
          <Col xs={24} md={8}>
            <Statistic title="売上合計" value={totalSales} suffix="万円" />
          </Col>
          <Col xs={24} md={8}>
            <Statistic
              title="最高売上"
              value={Math.max(...customers.map((c) => c.sales))}
              suffix="万円"
            />
          </Col>
        </Row>
      </div>
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "row",
          gap: 24,
          alignItems: "stretch",
          padding: 24,
          paddingTop: 0,
        }}
      >
        {/* 地図（左・大きめ） */}
        <Card
          style={{
            flex: 2.5,
            minWidth: 320,
            height: "auto",
            minHeight: 360,
            display: "flex",
            flexDirection: "column",
          }}
          styles={{
            body: {
              height: MAP_HEIGHT,
              display: "flex",
              flexDirection: "column",
              padding: 0,
            },
          }}
        >
          <h3 style={{ margin: "16px" }}>地図上の売上分布（関東一都三県）</h3>
          <div style={{ flex: 1, height: MAP_HEIGHT }}>
            <MapContainer
              center={[35.7, 139.7]}
              zoom={9}
              style={{ height: MAP_HEIGHT, width: "100%" }}
            >
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
                attribution="&copy; OpenStreetMap & CartoDB"
              />
              {/* 都道府県：極薄色＋太い黒線 */}
              {prefGeoJson && (
                <GeoJSON
                  data={prefGeoJson}
                  style={(feature) => ({
                    color: "#222",
                    weight: 1,
                    fillColor: getPrefColor(feature?.properties?.name || ""),
                    fillOpacity: 0.1,
                  })}
                />
              )}
              {/* ラベル */}
              {prefGeoJson &&
                prefGeoJson.features.map((feature, i: number) => {
                  const prop = feature.properties;
                  const label = prop?.name ?? "不明";
                  const [lat, lng] = getCenterOfGeometry(feature);
                  return (
                    <Marker
                      key={label + i}
                      position={[lat, lng]}
                      icon={L.divIcon({
                        className: "pref-label",
                        html: `<span style="
                                                    font-size:18px;
                                                    font-weight:bold;
                                                    color:#111;
                                                    text-shadow:0 0 4px #fff,0 1px 6px #fff,1px 1px 0 #fff,0 0 8px #fff;
                                                ">${label}</span>`,
                        iconSize: [110, 28],
                        iconAnchor: [55, 14],
                      })}
                      interactive={false}
                    />
                  );
                })}
              {/* 本社は赤ピン */}
              <Marker position={HQ_POSITION} icon={companyIcon}>
                <Popup>
                  <b>本社所在地</b>
                  <br />
                  〒XXX-XXXX 東京都江戸川区
                </Popup>
              </Marker>
              {/* バブル：カラースケールと完全連動 */}
              {customers.map((cust) => (
                <Circle
                  key={cust.id}
                  center={[cust.lat, cust.lng]}
                  radius={getRadius(cust.sales)}
                  fillColor={getColor(cust.sales)}
                  fillOpacity={0.34}
                  stroke={false}
                >
                  <Tooltip>
                    <div>
                      <strong>{cust.name}</strong>
                      <br />
                      売上: {cust.sales} 万円
                    </div>
                  </Tooltip>
                </Circle>
              ))}
            </MapContainer>
          </div>
          {/* バブル色凡例 */}
          <div
            style={{
              marginTop: 16,
              background: "rgba(255,255,255,0.9)",
              borderRadius: 8,
              padding: "8px 16px",
              boxShadow: "0 1px 6px #ddd",
              display: "flex",
              alignItems: "center",
            }}
          >
            <span style={{ fontWeight: "bold", fontSize: 15, marginRight: 8 }}>
              ■ バブル色凡例：
            </span>
            {colorScale.map((item) => (
              <span
                key={item.label}
                style={{
                  marginRight: 20,
                  display: "inline-flex",
                  alignItems: "center",
                }}
              >
                <span
                  style={{
                    display: "inline-block",
                    width: 18,
                    height: 18,
                    borderRadius: "50%",
                    backgroundColor: item.color,
                    marginRight: 5,
                    border: "1.5px solid #888",
                  }}
                />
                <span style={{ fontSize: 15 }}>{item.label}</span>
              </span>
            ))}
          </div>
        </Card>
        {/* 顧客ランキング（右） */}
        <Card
          style={{
            flex: 1,
            minWidth: 260,
            maxWidth: 420,
            height: "auto",
            minHeight: 360,
            display: "flex",
            flexDirection: "column",
          }}
          styles={{
            body: {
              height: MAP_HEIGHT,
              display: "flex",
              flexDirection: "column",
              padding: 0,
            },
          }}
        >
          <h3 style={{ margin: "16px" }}>顧客ランキング</h3>
          <div
            className="responsive-x"
            style={{ flex: 1, margin: "0 16px 16px 16px" }}
          >
            <Table
              dataSource={sortedCustomers}
              columns={columns}
              size="small"
              rowKey="id"
              pagination={false}
              scroll={{ y: MAP_HEIGHT - 90, x: "max-content" }}
            />
          </div>
        </Card>
      </div>
    </div>
  );
};

export default CustomerListDashboard;
