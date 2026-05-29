import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { RefreshCw, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import type { LeetCodeAccount, SyncResult } from "@/types/api";

const linkSchema = z.object({
  handle: z
    .string()
    .min(1, "Handle is required.")
    .regex(/^[a-zA-Z0-9_-]+$/, "Letters, digits, dashes, underscores only."),
});
type LinkInput = z.infer<typeof linkSchema>;

export function AccountPage() {
  const qc = useQueryClient();
  const [banner, setBanner] = useState<{ kind: "success" | "destructive"; msg: string } | null>(null);

  const accountQuery = useQuery({
    queryKey: ["leetcode", "account"],
    queryFn: async () => {
      try {
        const { data } = await api.get<LeetCodeAccount>("/leetcode/account/");
        return data;
      } catch (err) {
        if ((err as { response?: { status?: number } }).response?.status === 404) return null;
        throw err;
      }
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<LinkInput>({
    resolver: zodResolver(linkSchema),
    defaultValues: { handle: "" },
  });

  const linkMutation = useMutation({
    mutationFn: async (input: LinkInput) => {
      const { data } = await api.post<LeetCodeAccount>("/leetcode/account/", input);
      return data;
    },
    onSuccess: (data) => {
      qc.setQueryData(["leetcode", "account"], data);
      reset();
      setBanner({
        kind: data.is_verified ? "success" : "destructive",
        msg: data.is_verified
          ? `Linked & verified - ${data.total_solved} problems pulled.`
          : `Linked but verification failed: ${data.last_sync_error}`,
      });
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string; handle?: string[] } } })
          .response?.data;
      setBanner({
        kind: "destructive",
        msg: detail?.detail || detail?.handle?.[0] || "Failed to link handle.",
      });
    },
  });

  const syncMutation = useMutation({
    mutationFn: async () => {
      // Full sync can iterate many recent solves - bump the timeout past the
      // 30s default so a slow LeetCode response doesn't trip a false-failure.
      const { data } = await api.post<SyncResult>(
        "/leetcode/account/sync/",
        undefined,
        { timeout: 60_000 },
      );
      return data;
    },
    onSuccess: (data) => {
      qc.setQueryData(["leetcode", "account"], data.account);
      setBanner({
        kind: data.error ? "destructive" : "success",
        msg: data.error
          ? `Sync failed: ${data.error}`
          : `Synced - ${data.new_solves} new solves.`,
      });
    },
  });

  const unlinkMutation = useMutation({
    mutationFn: async () => api.delete("/leetcode/account/"),
    onSuccess: () => {
      qc.setQueryData(["leetcode", "account"], null);
      setBanner({ kind: "success", msg: "Handle unlinked." });
    },
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Account</h1>
        <p className="text-muted-foreground mt-1">
          Link your LeetCode handle so we can pull your solves automatically.
        </p>
      </div>

      {banner && <Alert variant={banner.kind}>{banner.msg}</Alert>}

      <Card>
        <CardHeader>
          <CardTitle>LeetCode integration</CardTitle>
          <CardDescription>
            We sync every 6 hours. You can also kick off a manual sync any time.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {accountQuery.data ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <Label className="text-xs text-muted-foreground">Handle</Label>
                  <p className="font-mono text-lg">{accountQuery.data.handle}</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => syncMutation.mutate()}
                    disabled={syncMutation.isPending}
                  >
                    <RefreshCw className={syncMutation.isPending ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
                    Sync now
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => unlinkMutation.mutate()}
                    disabled={unlinkMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4" />
                    Unlink
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <Label className="text-xs text-muted-foreground">Total</Label>
                  <p className="text-xl font-semibold">{accountQuery.data.total_solved}</p>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Status</Label>
                  <p className="text-xl font-semibold capitalize">{accountQuery.data.sync_status}</p>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Last sync</Label>
                  <p className="text-sm">
                    {accountQuery.data.last_synced_at
                      ? new Date(accountQuery.data.last_synced_at).toLocaleString()
                      : "-"}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <form
              onSubmit={handleSubmit((d) => linkMutation.mutate(d))}
              className="space-y-4"
            >
              <div className="space-y-2">
                <Label htmlFor="handle">LeetCode handle</Label>
                <Input
                  id="handle"
                  placeholder="anveet"
                  {...register("handle")}
                />
                {errors.handle && (
                  <p className="text-sm text-destructive">{errors.handle.message}</p>
                )}
              </div>
              <Button type="submit" disabled={linkMutation.isPending}>
                {linkMutation.isPending ? "Linking…" : "Link handle"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
