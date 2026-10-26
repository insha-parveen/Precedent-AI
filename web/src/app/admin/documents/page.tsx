import Link from 'next/link';
import { Badge } from '@/components/ui/badge';

export default function AdminDocuments() {
  return (
    <div className="p-6">
      <div className="flex justify-between items-start mb-6">
        <h1 className="text-2xl font-bold">Document Management</h1>
        <Link href="/admin/documents/upload" className="px-4 py-2 bg-primary/10 text-primary rounded hover:bg-primary/20">
          Upload Document
        </Link>
      </div>

      <div className="border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Documents in Corpus</h2>
        <p className="text-muted-foreground">Document listing will appear here once API endpoints are implemented.</p>
        <div className="mt-4 p-4 bg-muted/50 rounded">
          <p className="text-sm text-muted-foreground">
            This interface will allow you to:
          </p>
          <ul className="list-disc list-inside mt-2 space-y-1 text-sm text-muted-foreground">
            <li>View all documents with metadata (title, type, parties, date)</li>
            <li>Filter documents by source, type, or access group</li>
            <li>Search documents by content or metadata</li>
            <li>View document details including clauses and classifications</li>
            <li>Upload new documents (PDF, DOCX, TXT)</li>
            <li>Re-process or re-classify existing documents</li>
            <li>Delete or archive documents</li>
          </ul>
        </div>
      </div>
    </div>
  );
}