import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { PageHeader } from "@/components/PageHeader";
import { useAppStore } from "@/lib/store/useAppStore";
import { useState } from "react";
import { toast } from "@/hooks/use-toast";

const Profile = () => {
  const { user, setUser } = useAppStore();
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [organization, setOrganization] = useState(user?.organization ?? "");

  const save = () => {
    if (!user) return;
    setUser({ ...user, name, email, organization });
    toast({ title: "Profile updated" });
  };

  const initials = name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase() || "U";

  return (
    <div className="mx-auto w-full max-w-3xl">
      <PageHeader title="Profile" description="Manage your account information." />

      <Card>
        <CardHeader><CardTitle>Account</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16"><AvatarFallback className="bg-primary text-primary-foreground">{initials}</AvatarFallback></Avatar>
            <Button variant="outline" size="sm">Change photo</Button>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5"><Label>Full name</Label><Input value={name} onChange={(e) => setName(e.target.value)} /></div>
            <div className="space-y-1.5"><Label>Email</Label><Input value={email} onChange={(e) => setEmail(e.target.value)} /></div>
            <div className="space-y-1.5 sm:col-span-2"><Label>Organization</Label><Input value={organization} onChange={(e) => setOrganization(e.target.value)} /></div>
          </div>
          <div className="flex justify-end"><Button onClick={save}>Save changes</Button></div>
        </CardContent>
      </Card>

      <Card className="mt-6 border-destructive/40">
        <CardHeader><CardTitle className="text-destructive">Danger zone</CardTitle></CardHeader>
        <CardContent className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Delete account</p>
            <p className="text-xs text-muted-foreground">This permanently removes your data.</p>
          </div>
          <Button variant="destructive">Delete</Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default Profile;