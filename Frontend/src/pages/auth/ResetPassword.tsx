import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "@/hooks/use-toast";

const schema = z.object({
  password: z.string().min(8, "At least 8 characters").max(100),
  confirmPassword: z.string(),
}).refine((d) => d.password === d.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});
type FormValues = z.infer<typeof schema>;

const ResetPassword = () => {
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({ resolver: zodResolver(schema) });
  const onSubmit = async () => {
    toast({ title: "Password updated", description: "You can now sign in with your new password." });
    navigate("/login");
  };

  return (
    <div className="rounded-2xl border border-border/60 bg-card p-8 shadow-elegant">
      <h1 className="text-2xl font-bold tracking-tight">Set a new password</h1>
      <p className="mt-1 text-sm text-muted-foreground">Use at least 8 characters with a mix of letters and numbers.</p>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="password">New password</Label>
          <Input id="password" type="password" {...register("password")} />
          {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="confirmPassword">Confirm password</Label>
          <Input id="confirmPassword" type="password" {...register("confirmPassword")} />
          {errors.confirmPassword && <p className="text-xs text-destructive">{errors.confirmPassword.message}</p>}
        </div>
        <Button type="submit" className="w-full" disabled={isSubmitting}>Update password</Button>
      </form>
      <p className="mt-6 text-center text-sm">
        <Link to="/login" className="text-primary hover:underline">Back to sign in</Link>
      </p>
    </div>
  );
};

export default ResetPassword;