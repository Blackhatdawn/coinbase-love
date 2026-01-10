import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { Download, Filter, MoreVertical } from "lucide-react";

interface AuditLog {
  id: string;
  action: string;
  resource?: string;
  status: string;
  created_at: string;
  details?: Record<string, any>;
}

const AuditLogViewer = () => {
  const { toast } = useToast();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>("");
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  // Format action for display
  const formatAction = (action: string): string => {
    return action
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Get status badge color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-50';
      case 'failure':
        return 'text-red-600 bg-red-50';
      case 'pending':
        return 'text-yellow-600 bg-yellow-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  // Load audit logs
  useEffect(() => {
    const loadLogs = async () => {
      setIsLoading(true);
      try {
        const response = await api.auditLogs.getLogs(limit, offset, filter || undefined);
        setLogs(response.logs || []);
      } catch (error: any) {
        toast({
          title: "Failed to load audit logs",
          description: error.message,
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadLogs();
  }, [limit, offset, filter, toast]);

  // Export logs
  const handleExport = async () => {
    try {
      const response = await api.auditLogs.exportLogs();
      const element = document.createElement("a");
      element.setAttribute("href", `data:text/csv;charset=utf-8,${encodeURIComponent(response)}`);
      element.setAttribute("download", `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`);
      element.style.display = "none";
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      toast({
        title: "Exported",
        description: "Audit logs exported successfully",
      });
    } catch (error: any) {
      toast({
        title: "Export failed",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Security Audit Log</h3>
          <p className="text-sm text-muted-foreground">
            Track all sensitive activities on your account
          </p>
        </div>
        <Button onClick={handleExport} variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        <Input
          placeholder="Filter by action (login, logout, etc.)"
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value);
            setOffset(0);
          }}
          className="max-w-sm"
        />
        {filter && (
          <Button
            variant="ghost"
            onClick={() => {
              setFilter("");
              setOffset(0);
            }}
          >
            Clear
          </Button>
        )}
      </div>

      {/* Logs Table */}
      <div className="border rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-muted-foreground">
            Loading audit logs...
          </div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No audit logs found
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted">
                <tr>
                  <th className="text-left p-3 font-semibold">Timestamp</th>
                  <th className="text-left p-3 font-semibold">Action</th>
                  <th className="text-left p-3 font-semibold">Resource</th>
                  <th className="text-left p-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b hover:bg-muted/50 transition">
                    <td className="p-3">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="p-3 font-medium">
                      {formatAction(log.action)}
                    </td>
                    <td className="p-3 text-muted-foreground">
                      {log.resource || '—'}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(log.status)}`}>
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {logs.length > 0 && (
        <div className="flex justify-between items-center">
          <p className="text-sm text-muted-foreground">
            Showing {offset + 1} to {offset + logs.length}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - limit))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={logs.length < limit}
              onClick={() => setOffset(offset + limit)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogViewer;
