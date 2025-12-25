import React from "react";
import { Link, useLocation } from "react-router-dom";

export type RefItem = { title: string; section: string; url: string };

const References: React.FC<{ items: RefItem[] }> = ({ items }) => {
  const loc = useLocation();
  const backgroundLocation = loc;
  return (
    <div>
      <strong>参照:</strong>{" "}
      {items.map((r, i) => {
        const u = new URL(r.url, window.location.origin);
        const path = u.pathname + u.hash;
        return (
          <React.Fragment key={r.url}>
            <Link to={path} state={{ backgroundLocation }}>
              {r.title}（{r.section}）
            </Link>
            {i < items.length - 1 ? ", " : ""}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default References;
