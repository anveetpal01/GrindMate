import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Copy, Crown, Flame } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import type { Group, GroupInvite, LeaderboardResponse } from "@/types/api";

const PERIODS = ["daily", "weekly", "all-time"] as const;
type Period = (typeof PERIODS)[number];

export function GroupDetailPage() {
  const { publicId } = useParams<{ publicId: string }>();
  const [period, setPeriod] = useState<Period>("weekly");
  const [latestInvite, setLatestInvite] = useState<GroupInvite | null>(null);

  const groupQuery = useQuery({
    queryKey: ["groups", publicId],
    queryFn: async () => {
      const { data } = await api.get<Group>(`/groups/${publicId}/`);
      return data;
    },
    enabled: !!publicId,
  });

  const leaderboardQuery = useQuery({
    queryKey: ["groups", publicId, "leaderboard", period],
    queryFn: async () => {
      const { data } = await api.get<LeaderboardResponse>(
        `/groups/${publicId}/leaderboard/`,
        { params: { period } },
      );
      return data;
    },
    enabled: !!publicId,
  });

  const inviteMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<GroupInvite>(`/groups/${publicId}/invite/`);
      return data;
    },
    onSuccess: (data) => setLatestInvite(data),
  });

  const inviteUrl = latestInvite
    ? `${window.location.origin}/join/${latestInvite.token}`
    : null;

  return (
    <div className="space-y-6">
      {groupQuery.data && (
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              {groupQuery.data.name}
              {groupQuery.data.role === "admin" && (
                <Crown className="h-5 w-5 text-yellow-500" />
              )}
            </h1>
            {groupQuery.data.description && (
              <p className="text-muted-foreground mt-1">{groupQuery.data.description}</p>
            )}
          </div>
          {groupQuery.data.role === "admin" && (
            <Button onClick={() => inviteMutation.mutate()} disabled={inviteMutation.isPending}>
              {inviteMutation.isPending ? "Generating…" : "Invite link"}
            </Button>
          )}
        </div>
      )}

      {inviteUrl && (
        <Card>
          <CardContent className="p-4 flex items-center justify-between gap-4">
            <code className="text-sm break-all">{inviteUrl}</code>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigator.clipboard.writeText(inviteUrl)}
            >
              <Copy className="h-4 w-4" /> Copy
            </Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <div>
              <CardTitle>Leaderboard</CardTitle>
              <CardDescription>Difficulty-weighted score (Easy 1, Medium 3, Hard 5).</CardDescription>
            </div>
            <div className="flex gap-1 rounded-md border p-1">
              {PERIODS.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPeriod(p)}
                  className={
                    "px-3 py-1 text-sm rounded transition-colors " +
                    (period === p
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground")
                  }
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {leaderboardQuery.isLoading && (
            <p className="text-muted-foreground">Loading…</p>
          )}
          {leaderboardQuery.data && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-muted-foreground border-b">
                  <tr>
                    <th className="py-2 pr-4">#</th>
                    <th className="py-2 pr-4">User</th>
                    <th className="py-2 pr-4 text-right">Score</th>
                    <th className="py-2 pr-4 text-right">Solved</th>
                    <th className="py-2 pr-4 text-right">E / M / H</th>
                    <th className="py-2 pr-4 text-right">Streak</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboardQuery.data.rows.map((row) => (
                    <tr key={row.public_id} className="border-b last:border-0">
                      <td className="py-3 pr-4 font-mono">{row.rank}</td>
                      <td className="py-3 pr-4">
                        <div className="font-medium">{row.display_name}</div>
                        <div className="text-xs text-muted-foreground">@{row.username}</div>
                      </td>
                      <td className="py-3 pr-4 text-right font-semibold">{row.score}</td>
                      <td className="py-3 pr-4 text-right">{row.total_solved}</td>
                      <td className="py-3 pr-4 text-right text-xs">
                        <span className="text-green-600">{row.easy_solved}</span> /{" "}
                        <span className="text-yellow-600">{row.medium_solved}</span> /{" "}
                        <span className="text-red-600">{row.hard_solved}</span>
                      </td>
                      <td className="py-3 pr-4 text-right">
                        <span className="inline-flex items-center gap-1">
                          <Flame className="h-3.5 w-3.5 text-orange-500" />
                          {row.current_streak}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
