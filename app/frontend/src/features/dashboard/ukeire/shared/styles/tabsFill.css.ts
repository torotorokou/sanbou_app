/**
 * Tabs 高さ fix CSS
 * TabsコンポーネントをFlex高さ100%で描画するためのスタイル
 */

export const TABS_FILL_CLASS = "tabs-fill-100";

export const tabsFillCSS = `
.${TABS_FILL_CLASS} { height:100%; display:flex; flex-direction:column; min-height:0; }
.${TABS_FILL_CLASS} .ant-tabs-content-holder,
.${TABS_FILL_CLASS} .ant-tabs-content {
  height:100%;
  display:flex;
  flex-direction:column;
  min-height:0;
}
.${TABS_FILL_CLASS} .ant-tabs-tabpane { height:100%; min-height:0; }
.${TABS_FILL_CLASS} .ant-tabs-tabpane.ant-tabs-tabpane-active { display:flex; flex-direction:column; }
.${TABS_FILL_CLASS} .ant-tabs-tabpane:not(.ant-tabs-tabpane-active),
.${TABS_FILL_CLASS} .ant-tabs-tabpane[aria-hidden="true"] { display:none !important; }
`;
