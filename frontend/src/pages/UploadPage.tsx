import PageHeader from "../components/PageHeader";
import UploadPanel from "../features/upload/UploadPanel";

export default function UploadPage() {
  return (
    <section className="stack">
      <PageHeader
        title="Upload"
        description="Add local source documents and run the ingestion pipeline."
      />
      <UploadPanel />
    </section>
  );
}

