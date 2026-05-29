import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";

const schema = z.object({
  email: z.string().email("Enter a valid email."),
});
type Input = z.infer<typeof schema>;

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Input>({ resolver: zodResolver(schema), defaultValues: { email: "" } });

  const mutation = useMutation({
    mutationFn: async (data: Input) => api.post("/auth/password-reset/request/", data),
    onSuccess: () => setSent(true),
  });

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Forgot your password?</CardTitle>
          <CardDescription>
            Enter the email tied to your account and we'll send a reset link.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))}>
          <CardContent className="space-y-4">
            {sent ? (
              <Alert variant="success">
                If that email matches an account, a reset link is on the way.
                The link expires in 1 hour.
              </Alert>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" autoComplete="email" {...register("email")} />
                {errors.email && (
                  <p className="text-sm text-destructive">{errors.email.message}</p>
                )}
              </div>
            )}
          </CardContent>
          <CardFooter className="flex flex-col gap-3">
            {!sent && (
              <Button type="submit" className="w-full" disabled={mutation.isPending}>
                {mutation.isPending ? "Sending..." : "Send reset link"}
              </Button>
            )}
            <p className="text-sm text-muted-foreground text-center">
              <Link to="/login" className="text-primary hover:underline">
                Back to login
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
