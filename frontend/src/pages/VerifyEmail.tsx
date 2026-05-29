import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";

export function VerifyEmailPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token");
  const [state, setState] = useState<"pending" | "ok" | "error">(
    token ? "pending" : "error",
  );
  const [message, setMessage] = useState<string | null>(
    token ? null : "Missing verification token.",
  );

  useEffect(() => {
    if (!token) return;
    api
      .post("/auth/verify-email/", { token })
      .then(() => {
        setState("ok");
        setMessage("Email verified. You can log in now.");
        setTimeout(() => navigate("/login", { replace: true }), 1500);
      })
      .catch((err) => {
        setState("error");
        setMessage(
          err.response?.data?.detail ||
            "This verification link is invalid or expired.",
        );
      });
  }, [token, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Verifying email</CardTitle>
          <CardDescription>Just a moment...</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {state === "pending" && <p className="text-muted-foreground">Working on it...</p>}
          {state === "ok" && message && <Alert variant="success">{message}</Alert>}
          {state === "error" && message && (
            <>
              <Alert variant="destructive">{message}</Alert>
              <Link to="/login">
                <Button variant="outline" className="w-full">Back to login</Button>
              </Link>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
