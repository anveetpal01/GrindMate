import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { Trophy } from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PasswordInput } from "@/components/ui/PasswordInput";
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
import type { LoginResponse } from "@/types/api";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email."),
  password: z.string().min(1, "Password is required."),
});

type LoginInput = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((s) => s.setSession);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const [unverifiedEmail, setUnverifiedEmail] = useState<string | null>(null);

  const loginMutation = useMutation({
    mutationFn: async (input: LoginInput) => {
      const { data } = await api.post<LoginResponse>("/auth/login/", input);
      return data;
    },
    onSuccess: (data) => {
      setSession({ access: data.access, refresh: data.refresh }, data.user);
      const from =
        (location.state as { from?: { pathname?: string } } | null)?.from
          ?.pathname || "/dashboard";
      navigate(from, { replace: true });
    },
    onError: (err: unknown, variables) => {
      const message =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail || "Invalid email or password.";
      setServerError(message);
      if (message.toLowerCase().includes("verif")) {
        setUnverifiedEmail(variables.email);
      }
    },
  });

  const resendMutation = useMutation({
    mutationFn: async (email: string) =>
      api.post("/auth/resend-verification/", { email }),
    onSuccess: (_data, email) => {
      // Fresh code is on its way - take them to the OTP screen to enter it.
      navigate("/verify-otp", { state: { email } });
    },
  });

  const onSubmit = (input: LoginInput) => {
    setServerError(null);
    loginMutation.mutate(input);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto h-12 w-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center mb-2">
            <Trophy className="h-6 w-6" />
          </div>
          <CardTitle>Welcome back</CardTitle>
          <CardDescription>Log in to keep the streak alive.</CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            {serverError && (
              <Alert variant="destructive">
                <div className="space-y-2">
                  <p>{serverError}</p>
                  {unverifiedEmail && (
                    <button
                      type="button"
                      className="text-sm font-medium underline disabled:opacity-50"
                      onClick={() => resendMutation.mutate(unverifiedEmail)}
                      disabled={resendMutation.isPending}
                    >
                      {resendMutation.isPending
                        ? "Sending code..."
                        : "Send a new code and verify now"}
                    </button>
                  )}
                </div>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="anveet@grindmate.dev"
                autoComplete="email"
                {...register("email")}
              />
              {errors.email && (
                <p className="text-sm text-destructive">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-muted-foreground hover:text-primary hover:underline"
                >
                  Forgot?
                </Link>
              </div>
              <PasswordInput
                id="password"
                autoComplete="current-password"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-sm text-destructive">
                  {errors.password.message}
                </p>
              )}
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-3">
            <Button
              type="submit"
              className="w-full"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? "Logging in..." : "Log in"}
            </Button>
            <p className="text-sm text-muted-foreground text-center">
              <Link to="/forgot-password" className="text-primary hover:underline">
                Forgot password?
              </Link>
            </p>
            <p className="text-sm text-muted-foreground text-center">
              New here?{" "}
              <Link to="/signup" className="text-primary hover:underline">
                Create an account
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
