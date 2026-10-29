import { useEffect, useState } from 'react';
import { api, ApiError } from '../../api';
import { PageHeader } from '../../app/PageHeader';
import { Skeleton } from '../../Skeleton';
import { Editor } from './Editor';
import { ProjectStep, TemplateStep } from './Steps';
import type { EditorResponse } from './types';

// A new document (its steps, then the editor) or an existing one in the editor, from the API address the route gives:
// /api/editor/new/<group>?doc_type=&project_id=&template_id= or /api/editor/<id>?correct=1.

export default function EditorPage({ source, title }: { source: string; title: string }) {
  const [data, setData] = useState<EditorResponse | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    api.get<EditorResponse>(source).then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Couldn't load the form. Check your connection."));
  }, [source]);

  if (!data) {
    return (
      <>
        <PageHeader title={title} heading />
        {error ? <div className="ui"><p className="error" role="alert">{error}</p></div> : <Skeleton kind="page" label="Loading the form…" />}
      </>
    );
  }
  if (data.step === 'project') return <ProjectStep data={data} />;
  if (data.step === 'template') return <TemplateStep data={data} />;
  return <Editor data={data} />;
}
