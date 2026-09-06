"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { auth } from "@/lib/api";
import GoogleSignInButton from "@/components/GoogleSignInButton";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await auth.login({ email, password });
      localStorage.setItem("flowmind_token", res.data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not log in. Check your credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-paper flex items-center justify-center px-6">
      <div className="card p-8 w-full max-w-sm">
        <h1 className="font-display text-2xl text-ink mb-1">Welcome back</h1>
        <p className="text-slatetext text-sm mb-6">Log in to your FlowMind workspace.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-slatetext block mb-1">Email</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="text-sm text-slatetext block mb-1">Password</label>
            <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Logging in..." : "Log in"}
          </button>
        </form>

        <p className="text-sm text-slatetext mt-6">
          New here? <Link href="/signup" className="text-deep underline">Create an account</Link>
        </p>

        <div className="flex items-center gap-3 my-5">
          <span className="h-px bg-mist flex-1" />
          <span className="text-xs text-slatetext">or</span>
          <span className="h-px bg-mist flex-1" />
        </div>
        <GoogleSignInButton />
      </div>
    </main>
  );
}
