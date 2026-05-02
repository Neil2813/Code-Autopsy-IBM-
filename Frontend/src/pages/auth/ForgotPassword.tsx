import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState } from "react";
import { CheckCircle2 } from "lucide-react";

const schema = z.object({ email: z.string().trim().email("Enter a valid email").max(255) });
type FormValues = z.infer<typeof schema>;

const ForgotPassword = () => {
  const [sent, setSent] = useState(false);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({ resolver: zodResolver(schema) });
  const onSubmit = async () => setSent(true);

  return (
    <div className="rounded-2xl border border-border/60 bg-card p-8 shadow-elegant">
      {sent ? (
        <div className="text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-success" />
          <h1 className="mt-4 text-xl font-bold">Check your email</h1>
          <p className="mt-2 text-sm text-muted-foreground">If an account exists, we've sent reset instructions.</p>
          <Button variant="outline" className="mt-6" onClick={() => setSent(false)}>Resend email</Button>
          <div className="mt-4">
            <Link to="/login" className="text-sm text-primary hover:underline">Back to sign in</Link>
          </div>
        </div>
      ) : (
        <>
          <h1 className="text-2xl font-bold tracking-tight">Forgot password?</h1>
          <p className="mt-1 text-sm text-muted-foreground">We'll email you a reset link.</p>
          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" {...register("email")} />
              {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>Send reset link</Button>
          </form>
          <p className="mt-6 text-center text-sm">
            <Link to="/login" className="text-primary hover:underline">Back to sign in</Link>
          </p>
        </>
      )}
    </div>
  );
};

export default ForgotPassword;