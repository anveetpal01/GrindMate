import { useQuery } from "@tanstack/react-query";
import { Code2, Flame, ListChecks } from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { buttonVariants } from "@/components/ui/buttonVariants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import type { LeetCodeAccount } from "@/types/api";

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon: typeof Code2;
}) {
  return (
    <Card>
      <CardContent className="p-6 flex items-center gap-4">
        <div className="h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <div className="text-2xl font-bold">{value}</div>
          <div className="text-sm text-muted-foreground">{label}</div>
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  const accountQuery = useQuery({
    queryKey: ["leetcode", "account"],
    queryFn: async () => {
      try {
        const { data } = await api.get<LeetCodeAccount>("/leetcode/account/");
        return data;
      } catch (err) {
        const status = (err as { response?: { status?: number } }).response?.status;
        if (status === 404) return null;
        throw err;
      }
    },
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Welcome back, {user?.display_name || user?.username}
        </h1>
        <p className="text-muted-foreground mt-1">
          Yeh raha tera grind summary.
        </p>
      </div>

      {accountQuery.isLoading && (
        <p className="text-muted-foreground">Loading account…</p>
      )}

      {accountQuery.data === null && (
        <Alert>
          <div className="flex items-center justify-between gap-4">
            <span>
              Link your LeetCode handle to start tracking solves and join group
              leaderboards.
            </span>
            <Link to="/account" className={buttonVariants({ size: "sm" })}>
              Link handle
            </Link>
          </div>
        </Alert>
      )}

      {accountQuery.data && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <StatCard
              label="Total solved"
              value={accountQuery.data.total_solved}
              icon={ListChecks}
            />
            <StatCard
              label="LeetCode rank"
              value={accountQuery.data.ranking ?? "-"}
              icon={Flame}
            />
            <StatCard
              label="Linked handle"
              value={accountQuery.data.handle}
              icon={Code2}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Difficulty mix</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Easy</div>
                  <div className="text-2xl font-semibold text-green-600">
                    {accountQuery.data.easy_solved}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Medium</div>
                  <div className="text-2xl font-semibold text-yellow-600">
                    {accountQuery.data.medium_solved}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Hard</div>
                  <div className="text-2xl font-semibold text-red-600">
                    {accountQuery.data.hard_solved}
                  </div>
                </div>
              </div>
              {accountQuery.data.last_synced_at && (
                <p className="text-xs text-muted-foreground mt-4">
                  Last synced{" "}
                  {new Date(accountQuery.data.last_synced_at).toLocaleString()}
                </p>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
