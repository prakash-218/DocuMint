// Grey shapes where a screen's content will be, while it loads: the same layout classes as the screen itself, so it
// takes the same room and reflows the same way on a phone. templates/_skeletons.html draws the same shapes into the
// page before the JavaScript arrives; keep the two alike.
import type { CSSProperties, JSX } from 'react';

export type SkeletonKind = 'list' | 'page' | 'home' | 'doc' | 'form';

function Bone({ w = '100%', h = 12, style }: { w?: number | string; h?: number; style?: CSSProperties }) {
  return <span className="sk" style={{ width: w, height: h, ...style }} />;
}

const WIDTHS = ['62%', '48%', '71%', '55%', '66%', '44%', '58%', '69%'];

function Head({ title = 220, button = true }: { title?: number; button?: boolean }) {
  return (
    <div className="head">
      <div style={{ display: 'grid', gap: 10 }}><Bone w={title} h={26} /><Bone w={150} h={12} /></div>
      {button && <Bone w={128} h={34} style={{ borderRadius: 8 }} />}
    </div>
  );
}

function Lines({ count, gap = 12 }: { count: number; gap?: number }) {
  return (
    <div style={{ display: 'grid', gap }}>
      {Array.from({ length: count }, (_, i) => <Bone key={i} w={WIDTHS[i % WIDTHS.length]} />)}
    </div>
  );
}

function Card({ lines = 3, title = 120 }: { lines?: number; title?: number }) {
  return (
    <section className="card">
      <div className="card-h"><Bone w={title} h={14} /></div>
      <div className="card-b"><Lines count={lines} /></div>
    </section>
  );
}

function List() {
  return (
    <>
      <Head />
      <div className="tabs" style={{ paddingBottom: 10 }}>{[64, 58, 70, 76, 60].map((w, i) => <Bone key={i} w={w} h={30} />)}</div>
      <div className="toolbar"><Bone w="auto" h={34} style={{ flex: '1 1 200px' }} /><Bone w={150} h={34} /><Bone w={110} h={34} /></div>
      <div className="rows">
        <div className="rh"><Bone w="30%" h={10} /></div>
        {WIDTHS.map((w, i) => (
          <div key={i} className="rr" style={{ gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1.4fr) 80px 110px' }}>
            <div style={{ display: 'grid', gap: 6 }}><Bone w={w} h={13} /><Bone w="40%" h={10} /></div>
            <Bone w="70%" h={11} /><Bone w={56} h={18} style={{ borderRadius: 10 }} /><Bone w={84} h={13} style={{ justifySelf: 'end' }} />
          </div>
        ))}
      </div>
    </>
  );
}

function Doc() {
  return (
    <>
      <Head title={240} button={false} />
      <Bone h={56} style={{ marginTop: 16, borderRadius: 10 }} />
      <div className="stats" style={{ marginTop: 12 }}>{[0, 1, 2].map((i) => <Bone key={i} h={64} style={{ borderRadius: 10 }} />)}</div>
    </>
  );
}

function Page() {
  return (
    <>
      <Doc />
      <div className="cols">
        <div className="col-main"><Card lines={5} title={140} /><Card lines={3} /></div>
        <div className="col-side"><Card lines={4} title={90} /><Card lines={2} title={70} /></div>
      </div>
    </>
  );
}

function Home() {
  return (
    <>
      <Head title={260} />
      <div className="stats">{[0, 1, 2].map((i) => <Bone key={i} h={86} style={{ borderRadius: 10 }} />)}</div>
      <div className="home-cols">
        <Card lines={6} title={130} />
        <div className="col-side"><Card lines={4} title={90} /><Card lines={3} title={110} /></div>
      </div>
    </>
  );
}

function Form() {
  return (
    <div style={{ display: 'grid', gap: 14 }}>
      {[180, 260, 200, 320].map((w, i) => <div key={i} style={{ display: 'flex', gap: 12 }}><Bone w={60} /><Bone w={w} /></div>)}
      <Bone h={150} style={{ borderRadius: 8 }} />
      <Bone w={240} />
    </div>
  );
}

const SHAPES: Record<SkeletonKind, () => JSX.Element> = { list: List, page: Page, home: Home, doc: Doc, form: Form };

/** The shapes of a kind of screen, announced once to screen readers as label ("Loading the projects…"). */
export function Skeleton({ kind, label, ui = true }: { kind: SkeletonKind; label: string; ui?: boolean }) {
  const Shape = SHAPES[kind];
  return (
    <div className={`${ui ? 'ui ' : ''}skeleton`} aria-busy="true" role="status">
      <span className="sr-only">{label}</span>
      <div aria-hidden="true"><Shape /></div>
    </div>
  );
}
