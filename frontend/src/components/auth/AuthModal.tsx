"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { TextField } from "@/components/ui/TextField";
import { toast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/client";
import { authApi } from "@/lib/api/auth";
import { useAuth } from "@/store/auth";
import { useUi } from "@/store/ui";

// These rules mirror the backend (domain/auth_policy.py), which has the final say.
const emailSchema = z.object({ email: z.string().trim().email("Enter a valid email address.") });
const loginSchema = z.object({ password: z.string().min(1, "Enter your password.") });
const eighteenYearsAgo = () => {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 18);
  return d.toISOString().slice(0, 10);
};
const signupSchema = z.object({
  first_name: z.string().trim().min(1, "First name is required.").max(50),
  last_name: z.string().trim().min(1, "Last name is required.").max(50),
  date_of_birth: z
    .string()
    .min(1, "Enter your date of birth.")
    .refine((v) => v <= eighteenYearsAgo(), "You must be at least 18 years old to sign up."),
  password: z
    .string()
    .min(8, "Use at least 8 characters.")
    .regex(/^(?=.*[A-Za-z])(?=.*\d)/, "Include at least one letter and one number.")
    .refine((v) => new TextEncoder().encode(v).length <= 72, "Use at most 72 bytes."),
});

type Step = "email" | "login" | "signup";

/** "Log in or sign up": ask for the email, then show the password form or the sign-up form. */
export function AuthModal() {
  const open = useUi((s) => s.authModalOpen);
  // The flow only exists while the dialog is open, so it starts from the email step every time.
  return open ? <AuthFlow /> : null;
}

function AuthFlow() {
  const closeAuth = useUi((s) => s.closeAuth);
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");

  const title = step === "email" ? "Log in or sign up" : step === "login" ? "Log in" : "Finish signing up";
  return (
    <Modal
      open
      onClose={() => closeAuth("dismiss")}
      title={title}
      headerLeft={
        step === "email" ? undefined : (
          <button
            onClick={() => setStep("email")}
            aria-label="Back"
            className="grid size-8 place-items-center rounded-full hover:bg-surface"
          >
            <ArrowLeft size={16} />
          </button>
        )
      }
    >
      <div className="p-6">
        {step === "email" && (
          <EmailStep
            onNext={(value, exists) => {
              setEmail(value);
              setStep(exists ? "login" : "signup");
            }}
          />
        )}
        {step === "login" && <LoginStep email={email} />}
        {step === "signup" && <SignupStep email={email} />}
      </div>
    </Modal>
  );
}

function useFinishAuth() {
  const router = useRouter();
  const closeAuth = useUi((s) => s.closeAuth);
  return () => {
    const redirect = useUi.getState().redirectAfterAuth;
    closeAuth("success");
    if (redirect) router.push(redirect);
  };
}

function EmailStep({ onNext }: { onNext: (email: string, exists: boolean) => void }) {
  const form = useForm({ resolver: zodResolver(emailSchema), defaultValues: { email: "" } });
  const { errors, isSubmitting } = form.formState;

  const submit = form.handleSubmit(async ({ email }) => {
    try {
      onNext(email.toLowerCase(), await authApi.emailExists(email));
    } catch (error) {
      form.setError("email", { message: error instanceof ApiError ? error.detail : "Could not reach the server." });
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <h3 className="text-[22px] font-semibold">Welcome to Airbnb</h3>
      <TextField
        label="Email"
        type="email"
        autoComplete="email"
        autoFocus
        error={errors.email?.message}
        {...form.register("email")}
      />
      <p className="text-xs text-muted">
        We&apos;ll check whether you already have an account, then log you in or help you create one.
      </p>
      <Button type="submit" size="lg" fullWidth loading={isSubmitting}>
        Continue
      </Button>

      <div className="flex items-center gap-3 py-1 text-xs text-muted">
        <hr className="flex-1 border-line" /> or <hr className="flex-1 border-line" />
      </div>
      {["Google", "Apple", "Facebook"].map((provider) => (
        <Button
          key={provider}
          type="button"
          variant="secondary"
          size="lg"
          fullWidth
          onClick={() => toast.error(`Continue with ${provider} is coming soon`)}
        >
          Continue with {provider}
        </Button>
      ))}
    </form>
  );
}

function PasswordToggle({ shown, onToggle }: { shown: boolean; onToggle: () => void }) {
  return (
    <button type="button" onClick={onToggle} className="text-sm font-semibold underline">
      {shown ? "Hide" : "Show"}
    </button>
  );
}

function LoginStep({ email }: { email: string }) {
  const login = useAuth((s) => s.login);
  const finish = useFinishAuth();
  const [shown, setShown] = useState(false);
  const form = useForm({ resolver: zodResolver(loginSchema), defaultValues: { password: "" } });
  const { errors, isSubmitting } = form.formState;
  const { setFocus } = form;
  useEffect(() => setFocus("password"), [setFocus]);

  const submit = form.handleSubmit(async ({ password }) => {
    try {
      await login(email, password);
      finish();
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.code === "RATE_LIMITED"
            ? "Too many attempts. Please wait a minute and try again."
            : error.detail
          : "Could not reach the server.";
      form.setError("password", { message });
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <p className="text-sm text-muted">
        Logging in as <span className="font-semibold text-ink">{email}</span>
      </p>
      <TextField
        label="Password"
        type={shown ? "text" : "password"}
        autoComplete="current-password"
        autoFocus
        error={errors.password?.message}
        trailing={<PasswordToggle shown={shown} onToggle={() => setShown((v) => !v)} />}
        {...form.register("password")}
      />
      <Button type="submit" size="lg" fullWidth loading={isSubmitting}>
        Log in
      </Button>
    </form>
  );
}

function SignupStep({ email }: { email: string }) {
  const signup = useAuth((s) => s.signup);
  const finish = useFinishAuth();
  const [shown, setShown] = useState(false);
  const form = useForm({
    resolver: zodResolver(signupSchema),
    defaultValues: { first_name: "", last_name: "", date_of_birth: "", password: "" },
  });
  const { errors, isSubmitting } = form.formState;
  const { setFocus } = form;
  useEffect(() => setFocus("first_name"), [setFocus]);

  const submit = form.handleSubmit(async (values) => {
    try {
      await signup({ email, ...values });
      finish();
      toast.success("Welcome to Airbnb!");
    } catch (error) {
      if (error instanceof ApiError && error.code === "UNDER_AGE") {
        form.setError("date_of_birth", { message: error.detail });
      } else {
        form.setError("password", { message: error instanceof ApiError ? error.detail : "Could not reach the server." });
      }
    }
  });

  return (
    <form onSubmit={submit} className="space-y-3" noValidate>
      <div>
        <TextField label="First name on ID" autoComplete="given-name" autoFocus error={errors.first_name?.message} {...form.register("first_name")} />
        <TextField label="Last name on ID" className="mt-3" autoComplete="family-name" error={errors.last_name?.message} {...form.register("last_name")} />
      </div>
      <TextField
        label="Birthday"
        type="date"
        max={eighteenYearsAgo()}
        error={errors.date_of_birth?.message}
        {...form.register("date_of_birth")}
      />
      <p className="text-xs text-muted">To sign up, you need to be at least 18. Your birthday won&apos;t be shared with other people.</p>
      <TextField label="Email" value={email} readOnly tabIndex={-1} />
      <TextField
        label="Password"
        type={shown ? "text" : "password"}
        autoComplete="new-password"
        error={errors.password?.message}
        trailing={<PasswordToggle shown={shown} onToggle={() => setShown((v) => !v)} />}
        {...form.register("password")}
      />
      <p className="text-xs text-muted">
        By selecting <strong>Agree and continue</strong>, I agree to Airbnb&apos;s Terms of Service and acknowledge the
        Privacy Policy.
      </p>
      <Button type="submit" size="lg" fullWidth loading={isSubmitting}>
        Agree and continue
      </Button>
    </form>
  );
}
