import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Users } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { buttonVariants } from "@/components/ui/buttonVariants";
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
import type { Group, PaginatedResponse } from "@/types/api";

export function GroupsPage() {
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  const groupsQuery = useQuery({
    queryKey: ["groups"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Group>>("/groups/");
      return data.results;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (payload: { name: string; description: string }) => {
      const { data } = await api.post<Group>("/groups/", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["groups"] });
      setName("");
      setDescription("");
      setShowCreate(false);
      setError(null);
    },
    onError: (err: unknown) => {
      const data = (err as { response?: { data?: Record<string, unknown> } }).response?.data;
      const fallback = "Failed to create group.";
      const pick = (k: string) => {
        const v = data?.[k];
        if (Array.isArray(v) && v.length > 0) return String(v[0]);
        if (typeof v === "string") return v;
        return null;
      };
      setError(pick("name") ?? pick("detail") ?? fallback);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Groups</h1>
          <p className="text-muted-foreground mt-1">
            Compete with your circle on the leaderboard.
          </p>
        </div>
        <Button onClick={() => setShowCreate((v) => !v)}>
          <Plus className="h-4 w-4" />
          New group
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>Create a group</CardTitle>
            <CardDescription>You'll be the admin. Invite friends after.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && <Alert variant="destructive">{error}</Alert>}
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="NeetCode 150 Crew"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description (optional)</Label>
              <Input
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Daily grind, weekly challenges."
              />
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => createMutation.mutate({ name, description })}
                disabled={!name.trim() || createMutation.isPending}
              >
                {createMutation.isPending ? "Creating…" : "Create"}
              </Button>
              <Button variant="ghost" onClick={() => setShowCreate(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {groupsQuery.isLoading && <p className="text-muted-foreground">Loading groups…</p>}

      {groupsQuery.data && groupsQuery.data.length === 0 && !showCreate && (
        <Alert>
          You're not in any groups yet. Create one above, or ask a friend for an invite link.
        </Alert>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {groupsQuery.data?.map((g) => (
          <Card key={g.public_id}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-muted-foreground" />
                {g.name}
              </CardTitle>
              {g.description && <CardDescription>{g.description}</CardDescription>}
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{g.member_count} members</span>
                <Link
                  to={`/groups/${g.public_id}`}
                  className={buttonVariants({ variant: "outline", size: "sm" })}
                >
                  Open →
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
