import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";

export function JoinPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<"pending" | "success" | "error">("pending");
  const [message, setMessage] = useState<string | null>(null);
  const [groupId, setGroupId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .post(`/groups/join/${token}/`)
      .then((r) => {
        setStatus("success");
        setGroupId(r.data.public_id);
        setMessage(`You're in: ${r.data.name}.`);
      })
      .catch((err) => {
        setStatus("error");
        setMessage(
          err.response?.data?.detail || "This invite is invalid or expired.",
        );
      });
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Join group</CardTitle>
          <CardDescription>Following the invite link…</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {status === "pending" && (
            <p className="text-muted-foreground">Verifying invite…</p>
          )}
          {status === "success" && message && (
            <>
              <Alert variant="success">{message}</Alert>
              <Button onClick={() => navigate(`/groups/${groupId}`)} className="w-full">
                Open group
              </Button>
            </>
          )}
          {status === "error" && message && (
            <>
              <Alert variant="destructive">{message}</Alert>
              <Button variant="outline" onClick={() => navigate("/groups")} className="w-full">
                Go to groups
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
