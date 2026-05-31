export default function UploadPage() {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-semibold mb-1">Upload</h1>
        <p className="text-muted-foreground text-sm mb-8">Ingest documents into the RAG pipeline</p>
        <div className="rounded-lg border-2 border-dashed border-border bg-card flex flex-col items-center justify-center h-64 gap-3">
          <p className="text-muted-foreground text-sm">Drop files here or click to upload</p>
        </div>
      </div>
    );
  }