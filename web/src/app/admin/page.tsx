import Link from 'next/link';
import { Badge } from '@/components/ui/badge';

export default function AdminDashboard() {
  return (
    <div className="p-6 space-y-8">
      <h1 className="text-3xl font-bold">Admin Dashboard</h1>
      <p className="text-lg text-muted-foreground">
        Manage your Precedent system configuration, documents, users, and monitoring.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link href="/admin/documents" className="group">
          <div className="border rounded-lg p-6 hover:border-primary/50 transition-border group-hover:border-primary/50">
            <h2 className="text-xl font-semibold mb-2 flex items-center">
              <Badge variant="secondary">Documents</Badge>&nbsp;Document Management
            </h2>
            <p className="text-muted-foreground">
              Upload, manage, and organize contract documents in your corpus.
            </p>
          </div>
        </Link>

        <Link href="/admin/taxonomy" className="group">
          <div className="border rounded-lg p-6 hover:border-primary/50 transition-border group-hover:border-primary/50">
            <h2 className="text-xl font-semibold mb-2 flex items-center">
              <Badge variant="secondary">Taxonomy</Badge>&nbsp;Category Management
            </h2>
            <p className="text-muted-foreground">
              Create and manage custom clause classification taxonomies.
            </p>
          </div>
        </Link>

        <Link href="/admin/users" className="group">
          <div className="border rounded-lg p-6 hover:border-primary/50 transition-border group-hover:border-primary/50">
            <h2 className="text-xl font-semibold mb-2 flex items-center">
              <Badge variant="secondary">Users</Badge>&nbsp;Access Control
            </h2>
            <p className="text-muted-foreground">
              Manage user accounts, roles, and access permissions.
            </p>
          </div>
        </Link>

        <Link href="/admin/monitoring" className="group">
          <div className="border rounded-lg p-6 hover:border-primary/50 transition-border group-hover:border-primary/50">
            <h2 className="text-xl font-semibold mb-2 flex items-center">
              <Badge variant="secondary">Monitoring</Badge>&nbsp;System Health
            </h2>
            <p className="text-muted-foreground">
              View system metrics, logs, and health status.
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
}