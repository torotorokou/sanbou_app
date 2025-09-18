export type TocItem = { level: 2 | 3; title: string; anchor: string };

export function ensureSectionAnchors(root: HTMLElement): TocItem[] {
  const hs = Array.from(root.querySelectorAll('h2, h3')) as HTMLElement[];
  let count = 0;
  const toc: TocItem[] = [];
  hs.forEach((el) => {
    const level = el.tagName.toLowerCase() === 'h2' ? 2 : 3;
    if (!el.id || !/^s-\d+$/.test(el.id)) {
      count += 1;
      el.id = `s-${count}`;
    }
    toc.push({ level: level as 2 | 3, title: el.textContent || '', anchor: el.id });
  });
  return toc;
}

export function smoothScrollToAnchor(container: HTMLElement | Window, anchor: string) {
  const id = anchor.startsWith('#') ? anchor.slice(1) : anchor;
  const target = document.getElementById(id);
  if (!target) return;
  const y = target.getBoundingClientRect().top + (container instanceof Window ? window.scrollY : (container as HTMLElement).scrollTop);
  const top = y - 80; // ヘッダ分のオフセット
  if (container instanceof Window) {
    window.scrollTo({ top, behavior: 'smooth' });
  } else {
    (container as HTMLElement).scrollTo({ top, behavior: 'smooth' });
  }
}
