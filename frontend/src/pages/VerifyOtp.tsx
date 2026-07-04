import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { MailCheck } from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
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
import type { LoginResponse } from "@/types/api";

const otpSchema = z.object({
  email: z.string().email("Enter a valid email."),
  otp: z.string().regex(/^\d{6}$/, "Enter the 6-digit code."),
});

type OtpInput = z.infer<typeof otpSchema>;

export function VerifyOtpPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((s) => s.setSession);
  const [serverError, setServerError] = useState<string | null>(null);
  const [resentBanner, setResentBanner] = useState<string | null>(null);

  // Email arrives via router state from the signup page; the field stays
  // editable as a fallback for users who land here directly.
  const prefilledEmail =
    (location.state as { email?: string } | null)?.email ?? "";

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm<OtpInput>({
    resolver: zodResolver(otpSchema),
    defaultValues: { email: prefilledEmail, otp: "" },
  });

  const verifyMutation = useMutation({
    mutationFn: async (input: OtpInput) => {
      const { data } = await api.post<LoginResponse>("/auth/verify-otp/", input);
      return data;
    },
    onSuccess: (data) => {
      setSession({ access: data.access, refresh: data.refresh }, data.user);
      navigate("/dashboard", { replace: true });
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail || "Verification failed. Please try again.";
      setServerError(message);
    },
  });

  const resendMutation = useMutation({
    mutationFn: async (email: string) =>
      api.post("/auth/resend-verification/", { email }),
    onSuccess: () => {
      setServerError(null);
      setResentBanner("New code sent. Check your inbox (or spam).");
    },
  });

  const onSubmit = (input: OtpInput) => {
    setServerError(null);
    setResentBanner(null);
    verifyMutation.mutate(input);
  };

  const handleResend = () => {
    const email = getValues("email");
    if (email) resendMutation.mutate(email);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto h-12 w-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center mb-2">
            <MailCheck className="h-6 w-6" />
          </div>
          <CardTitle>Check your email</CardTitle>
          <CardDescription>
            We sent a 6-digit code{prefilledEmail ? ` to ${prefilledEmail}` : ""}.
            Enter it below to finish signing up.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            {resentBanner && <Alert variant="success">{resentBanner}</Alert>}
            {serverError && <Alert variant="destructive">{serverError}</Alert>}

            {!prefilledEmail && (
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...register("email")}
                />
                {errors.email && (
                  <p className="text-sm text-destructive">{errors.email.message}</p>
                )}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="otp">Verification code</Label>
              <Input
                id="otp"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                placeholder="123456"
                className="text-center text-2xl tracking-[0.5em] font-mono"
                autoFocus
                {...register("otp")}
              />
              {errors.otp && (
                <p className="text-sm text-destructive">{errors.otp.message}</p>
              )}
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-3">
            <Button
              type="submit"
              className="w-full"
              disabled={verifyMutation.isPending}
            >
              {verifyMutation.isPending ? "Verifying…" : "Verify and continue"}
            </Button>
            <button
              type="button"
              className="text-sm text-muted-foreground hover:text-primary hover:underline disabled:opacity-50"
              onClick={handleResend}
              disabled={resendMutation.isPending}
            >
              {resendMutation.isPending ? "Sending…" : "Didn't get it? Resend code"}
            </button>
            <p className="text-sm text-muted-foreground text-center">
              Wrong account?{" "}
              <Link to="/signup" className="text-primary hover:underline">
                Sign up again
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
