import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAppStore } from "@/lib/store/useAppStore";
import { toast } from "@/hooks/use-toast";

const schema = z.object({
  name: z.string().trim().min(2, "Enter your full name").max(100),
  email: z.string().trim().email("Enter a valid email").max(255),
  organization: z.string().trim().max(100).optional(),
  role: z.string().min(1, "Select a role"),
  password: z.string().min(8, "At least 8 characters").max(100),
  confirmPassword: z.string(),
  terms: z.literal(true, { message: "You must accept the terms" }),
}).refine((d) => d.password === d.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});
type FormValues = z.infer<typeof schema>;

const strengthLabel = (pw: string) => {
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return ["Too weak", "Weak", "Fair", "Good", "Strong"][score];
};

const Register = () => {
  const setUser = useAppStore((s) => s.setUser);
  const navigate = useNavigate();
  const { register, handleSubmit, watch, setValue, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { role: "developer" },
  });
  const pw = watch("password") ?? "";

  const onSubmit = async (values: FormValues) => {
    setUser({ id: "local", name: values.name, email: values.email, role: values.role, organization: values.organization });
    toast({ title: "Account created", description: "Welcome to Code Autopsy." });
    navigate("/dashboard");
  };

  return (
    <div className="rounded-2xl border border-border/60 bg-card p-8 shadow-elegant">
      <h1 className="text-2xl font-bold tracking-tight">Create your account</h1>
      <p className="mt-1 text-sm text-muted-foreground">Start analyzing legacy code in minutes.</p>
      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="name">Full name</Label>
            <Input id="name" {...register("name")} />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" {...register("email")} />
            {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="organization">Organization</Label>
            <Input id="organization" {...register("organization")} />
          </div>
          <div className="space-y-1.5">
            <Label>Role</Label>
            <Select defaultValue="developer" onValueChange={(v) => setValue("role", v)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="developer">Developer</SelectItem>
                <SelectItem value="architect">Architect</SelectItem>
                <SelectItem value="manager">Manager</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" {...register("password")} />
          {pw && (
            <div className="flex items-center gap-2">
              <div className="h-1 flex-1 rounded-full bg-secondary">
                <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${(["Too weak","Weak","Fair","Good","Strong"].indexOf(strengthLabel(pw))+1) * 20}%` }} />
              </div>
              <span className="text-xs text-muted-foreground">{strengthLabel(pw)}</span>
            </div>
          )}
          {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="confirmPassword">Confirm password</Label>
          <Input id="confirmPassword" type="password" {...register("confirmPassword")} />
          {errors.confirmPassword && <p className="text-xs text-destructive">{errors.confirmPassword.message}</p>}
        </div>
        <div className="flex items-start gap-2">
          <Checkbox id="terms" onCheckedChange={(c) => setValue("terms", (c === true) as true, { shouldValidate: true })} />
          <Label htmlFor="terms" className="text-sm font-normal text-muted-foreground">
            I agree to the Terms of Service and Privacy Policy.
          </Label>
        </div>
        {errors.terms && <p className="text-xs text-destructive">{errors.terms.message as string}</p>}
        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating account..." : "Create account"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-primary hover:underline">Sign in</Link>
      </p>
    </div>
  );
};

export default Register;