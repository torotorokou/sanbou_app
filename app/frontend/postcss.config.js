import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default {
  plugins: {
    "postcss-import": {
      resolve(id) {
        // @/ を src/ に解決
        if (id.startsWith("@/")) {
          return path.resolve(__dirname, "src", id.slice(2));
        }
        return id;
      },
    },
    "postcss-custom-media": {
      preserve: false, // 生成物は標準の @media のみにする
    },
  },
};
