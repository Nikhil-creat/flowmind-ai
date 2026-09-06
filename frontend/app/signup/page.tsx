"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { auth } from "@/lib/api";
import GoogleSignInButton from "@/components/GoogleSignInButton";

export default function SignupPage() {
  const router = useRouter();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", company: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await auth.signup(form);
      localStorage.setItem("flowmind_token", res.data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not create your account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-paper flex items-center justify-center px-6">
      <div className="card p-8 w-full max-w-sm">
        <h1 className="font-display text-2xl text-ink mb-1">Create your workspace</h1>
        <p className="text-slatetext text-sm mb-6">Free to start - no card required.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-slatetext block mb-1">Full name</label>
            <input required value={form.full_name} onChange={(e) => update("full_name", e.target.value)} />
          </div>
          <div>
            <label className="text-sm text-slatetext block mb-1">Work email</label>
            <input type="email" required value={form.email} onChange={(e) => update("email", e.target.value)} />
          </div>
          <div>
            <label className="text-sm text-slatetext block mb-1">Company (optional)</label>
            <input value={form.company} onChange={(e) => update("company", e.target.value)} />
          </div>
          <div>
            <label className="text-sm text-slatetext block mb-1">Password</label>
            <input type="password" required minLength={8} value={form.password} onChange={(e) => update("password", e.target.value)} />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="text-sm text-slatetext mt-6">
          Already have an account? <Link href="/login" className="text-deep underline">Log in</Link>
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
