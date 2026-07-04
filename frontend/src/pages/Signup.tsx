import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { Trophy } from "lucide-react";
import { api } from "@/lib/api";
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

const signupSchema = z
  .object({
    email: z.string().email("Enter a valid email."),
    username: z
      .string()
      .min(3, "Min 3 characters.")
      .max(30, "Max 30 characters.")
      .regex(/^[a-zA-Z0-9_]+$/, "Letters, digits, underscores only."),
    display_name: z.string().max(80),
    password: z.string().min(8, "At least 8 characters."),
    password_confirm: z.string(),
  })
  .refine((d) => d.password === d.password_confirm, {
    path: ["password_confirm"],
    message: "Passwords do not match.",
  });

type SignupInput = z.infer<typeof signupSchema>;

export function SignupPage() {
  const navigate = useNavigate();
  const [serverErrors, setServerErrors] = useState<string[] | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupInput>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      email: "",
      username: "",
      display_name: "",
      password: "",
      password_confirm: "",
    },
  });

  const signupMutation = useMutation({
    mutationFn: async (input: SignupInput) => {
      const { data } = await api.post("/auth/register/", input);
      return data;
    },
    onSuccess: (_data, variables) => {
      navigate("/verify-otp", { replace: true, state: { email: variables.email } });
    },
    onError: (err: unknown) => {
      const data = (err as { response?: { data?: Record<string, unknown> } })
        .response?.data;
      if (data && typeof data === "object") {
        const messages = Object.entries(data).flatMap(([k, v]) =>
          (Array.isArray(v) ? v : [v]).map((m) => `${k}: ${m}`),
        );
        setServerErrors(messages);
      } else {
        setServerErrors(["Something went wrong. Please try again."]);
      }
    },
  });

  const onSubmit = (input: SignupInput) => {
    setServerErrors(null);
    signupMutation.mutate(input);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto h-12 w-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center mb-2">
            <Trophy className="h-6 w-6" />
          </div>
          <CardTitle>Start grinding</CardTitle>
          <CardDescription>
            Create an account to track your DSA progress with friends.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            {serverErrors && (
              <Alert variant="destructive">
                <ul className="list-disc pl-4 space-y-1">
                  {serverErrors.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" autoComplete="email" {...register("email")} />
              {errors.email && (
                <p className="text-sm text-destructive">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                placeholder="anveet"
                autoComplete="username"
                {...register("username")}
              />
              {errors.username && (
                <p className="text-sm text-destructive">{errors.username.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="display_name">Display name (optional)</Label>
              <Input
                id="display_name"
                placeholder="Anveet"
                {...register("display_name")}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <PasswordInput
                id="password"
                autoComplete="new-password"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-sm text-destructive">{errors.password.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password_confirm">Confirm password</Label>
              <PasswordInput
                id="password_confirm"
                autoComplete="new-password"
                {...register("password_confirm")}
              />
              {errors.password_confirm && (
                <p className="text-sm text-destructive">
                  {errors.password_confirm.message}
                </p>
              )}
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-3">
            <Button
              type="submit"
              className="w-full"
              disabled={signupMutation.isPending}
            >
              {signupMutation.isPending ? "Creating…" : "Create account"}
            </Button>
            <p className="text-sm text-muted-foreground text-center">
              Already have an account?{" "}
              <Link to="/login" className="text-primary hover:underline">
                Log in
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
