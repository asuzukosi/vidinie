"use client";

import { useEffect, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarImage } from "@/components/ui/avatar";
import client from "@/lib/sdk/client";
import { toast } from "sonner";
import { LoadingPage } from "@/components/utils/LoadingPage";
import type { RootState } from "@/lib/store/store";
import { setUser } from "@/lib/store/slices/authSlice";

export default function ProfilePage() {
  const user = useSelector((state: RootState) => state.auth.user);
  const dispatch = useDispatch();
  const [isSaving, setIsSaving] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
  });
  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  useEffect(() => {
    if (user) {
      setFormData({
        email: user.email || "",
      });
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // check if there are any changes
    if (formData.email === user?.email) {
      toast.info("No changes to save");
      return;
    }

    setIsSaving(true);
    try {
      const updatedUser = await client.updateUser({
        email: formData.email !== user?.email ? formData.email : undefined,
      });

      // update Redux state with the updated user data
      dispatch(setUser({
        id: updatedUser.id,
        email: updatedUser.email,
        token: user?.token || "",
        created_at: updatedUser.created_at,
        updated_at: updatedUser.updated_at,
        is_verified: updatedUser.is_verified,
        current_subscription: updatedUser.current_subscription,
        profile_picture: updatedUser.profile_picture,
      }));

      toast.success("Profile updated successfully");
    } catch (error: any) {
      toast.error("Failed to update profile", {
        description: error.message,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error("Passwords do not match", {
        description: "Please make sure both new passwords are the same.",
      });
      return;
    }

    if (passwordData.newPassword.length < 8) {
      toast.error("Password too short", {
        description: "Password must be at least 8 characters long.",
      });
      return;
    }

    setIsChangingPassword(true);
    try {
      await client.changePassword(passwordData.currentPassword, passwordData.newPassword);
      toast.success("Password changed successfully");
      setPasswordData({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
    } catch (error: any) {
      toast.error("Failed to change password", {
        description: error.message,
      });
    } finally {
      setIsChangingPassword(false);
    }
  };

  if (!user) {
    return <LoadingPage />;
  }


  
  const profilePictureUrl = user.profile_picture 
    ? client.getProfilePictureUrl(user.profile_picture)
    : null;

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Profile</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account information and preferences
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
          <CardDescription>
            Update your personal information and account details
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <FieldGroup>
              <Field>
                <FieldLabel>Profile Picture</FieldLabel>
                <div className="flex items-center gap-4">
                  <Avatar className="h-20 w-20">
                    <AvatarImage src={profilePictureUrl || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.email || "User")}&background=random`} />
                  </Avatar>
                  <div>
                    <Button type="button" variant="outline" size="sm">
                      Change Photo
                    </Button>
                    <FieldDescription className="mt-1">
                      JPG, GIF or PNG. Max size of 2MB
                    </FieldDescription>
                  </div>
                </div>
              </Field>

              <Field>
                <FieldLabel htmlFor="email">Email</FieldLabel>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  placeholder="Enter your email"
                />
                <FieldDescription>
                  Your email address is used for account notifications
                </FieldDescription>
              </Field>

              <Field>
                <FieldLabel>Account Status</FieldLabel>
                <div className="flex items-center gap-2">
                  <span className="text-sm">
                    {user.is_verified ? (
                      <span className="text-green-600 dark:text-green-400">
                        Verified
                      </span>
                    ) : (
                      <span className="text-yellow-600 dark:text-yellow-400">
                        Unverified
                      </span>
                    )}
                  </span>
                </div>
                <FieldDescription>
                  {user.is_verified
                    ? "Your account has been verified"
                    : "Please verify your email address"}
                </FieldDescription>
              </Field>

              <Field>
                <FieldLabel>Subscription Plan</FieldLabel>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium capitalize">
                    {user.current_subscription || "Free"}
                  </span>
                </div>
                <FieldDescription>
                  Manage your subscription in Settings
                </FieldDescription>
              </Field>

              <Field>
                <FieldLabel>Member Since</FieldLabel>
                <div className="text-sm text-muted-foreground">
                  {user.created_at
                    ? new Date(user.created_at).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })
                    : "N/A"}
                </div>
              </Field>

              <Field>
                <Button type="submit" disabled={isSaving}>
                  {isSaving ? "Saving..." : "Save Changes"}
                </Button>
              </Field>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Change Password</CardTitle>
          <CardDescription>
            Update your password to keep your account secure
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordChange}>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="current-password">Current Password</FieldLabel>
                <Input
                  id="current-password"
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, currentPassword: e.target.value })
                  }
                  placeholder="Enter your current password"
                  required
                />
                <FieldDescription>
                  Enter your current password to verify your identity
                </FieldDescription>
              </Field>

              <Field>
                <FieldLabel htmlFor="new-password">New Password</FieldLabel>
                <Input
                  id="new-password"
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, newPassword: e.target.value })
                  }
                  placeholder="Enter your new password"
                  required
                  minLength={8}
                />
                <FieldDescription>
                  Must be at least 8 characters long
                </FieldDescription>
              </Field>

              <Field>
                <FieldLabel htmlFor="confirm-password">Confirm New Password</FieldLabel>
                <Input
                  id="confirm-password"
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, confirmPassword: e.target.value })
                  }
                  placeholder="Confirm your new password"
                  required
                  minLength={8}
                />
                <FieldDescription>
                  Please confirm your new password
                </FieldDescription>
              </Field>

              <Field>
                <Button type="submit" disabled={isChangingPassword}>
                  {isChangingPassword ? "Changing Password..." : "Change Password"}
                </Button>
              </Field>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
