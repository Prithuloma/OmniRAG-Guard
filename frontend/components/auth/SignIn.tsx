"use client";

import { useAuth } from "@/context/AuthContext";
import { useState } from "react";
import { Shield, Loader, Mail, Lock, Sparkles, ArrowRight, UserPlus, LogIn } from "lucide-react";

export default function SignIn() {
  const { loginWithGoogle, loginWithEmail, signUpWithEmail } = useAuth();
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);
  const [error, setError] = useState("");

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("Please fill in all fields.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoggingIn(true);
    setError("");

    try {
      if (isSignUp) {
        await signUpWithEmail(email, password);
      } else {
        await loginWithEmail(email, password);
      }
    } catch (err: any) {
      let msg = err.message || "Authentication failed. Please check credentials.";
      if (err.code === "auth/user-not-found") {
        msg = "No user found with this email. Please sign up.";
      } else if (err.code === "auth/wrong-password") {
        msg = "Incorrect password. Please try again.";
      } else if (err.code === "auth/email-already-in-use") {
        msg = "This email is already registered. Try signing in.";
      } else if (err.code === "auth/invalid-email") {
        msg = "Invalid email format.";
      }
      setError(msg);
    } finally {
      setLoggingIn(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setLoggingIn(true);
    setError("");
    try {
      await loginWithGoogle();
    } catch (err: any) {
      setError(err.message || "Failed to sign in with Google.");
    } finally {
      setLoggingIn(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-slate-950 overflow-hidden font-sans">
      {/* Background decoration */}
      <div className="absolute top-[-30%] left-[-20%] w-[800px] h-[800px] rounded-full bg-violet-950/20 blur-[160px] pointer-events-none" />
      <div className="absolute bottom-[-30%] right-[-20%] w-[800px] h-[800px] rounded-full bg-indigo-950/20 blur-[160px] pointer-events-none" />

      {/* Main Container */}
      <div className="relative z-10 w-full max-w-md p-8 mx-4 bg-slate-900/45 border border-slate-800/60 rounded-2xl shadow-2xl backdrop-blur-xl transition-all duration-300">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-indigo-500/10 text-indigo-400 mb-4 border border-indigo-500/20 shadow-inner pulsing-ring">
            <Shield className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-2 flex items-center justify-center gap-1.5">
            <span>OmniRAG-Guard</span>
            <Sparkles className="w-4 h-4 text-amber-400 fill-amber-400/20" />
          </h1>
          <p className="text-muted-foreground text-xs max-w-xs mx-auto leading-relaxed">
            Secure, verified document retrieval. Grounded answers backed by cryptographic consensus.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-3.5 rounded-xl bg-red-950/45 border border-red-800/40 text-red-300 text-xs text-center leading-normal animate-pulse">
            {error}
          </div>
        )}

        <form onSubmit={handleEmailAuth} className="space-y-4 mb-6">
          <div className="space-y-1">
            <label className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider pl-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground/60" />
              <input
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loggingIn}
                className="w-full pl-10 pr-4 py-3 bg-slate-950/50 border border-slate-800 rounded-xl text-xs text-white placeholder:text-muted-foreground/45 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all"
                required
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider pl-1">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground/60" />
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loggingIn}
                className="w-full pl-10 pr-4 py-3 bg-slate-950/50 border border-slate-800 rounded-xl text-xs text-white placeholder:text-muted-foreground/45 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loggingIn}
            className="w-full py-3.5 rounded-xl bg-primary text-primary-foreground font-semibold text-xs tracking-wide shadow-lg shadow-primary/10 hover:opacity-95 active:translate-y-px transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:pointer-events-none"
          >
            {loggingIn ? (
              <Loader className="w-3.5 h-3.5 animate-spin" />
            ) : isSignUp ? (
              <>
                <UserPlus className="w-3.5 h-3.5" />
                <span>Create Workspace Account</span>
              </>
            ) : (
              <>
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In with Credentials</span>
              </>
            )}
          </button>
        </form>

        {/* Divider */}
        <div className="relative flex items-center justify-center my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-800" />
          </div>
          <span className="relative px-3 bg-[#0a0d14] text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
            Or continue with
          </span>
        </div>

        {/* Google Provider Button */}
        <button
          onClick={handleGoogleSignIn}
          disabled={loggingIn}
          className="w-full flex items-center justify-center gap-3 px-5 py-3.5 rounded-xl border border-slate-800 bg-slate-950/50 hover:bg-slate-900/60 text-white font-medium text-xs transition-all duration-200 focus:outline-none focus:ring-1 focus:ring-primary hover:border-slate-700 disabled:opacity-75 disabled:cursor-not-allowed group shadow-md"
        >
          {loggingIn ? (
            <Loader className="w-4 h-4 animate-spin text-primary" />
          ) : (
            <svg className="w-4 h-4 group-hover:scale-105 transition-transform duration-200" viewBox="0 0 24 24" width="24" height="24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                fill="#EA4335"
              />
            </svg>
          )}
          <span>Google Workspace Account</span>
        </button>

        {/* Toggle Account Mode */}
        <div className="mt-8 text-center">
          <button
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError("");
            }}
            className="text-[11px] font-medium text-primary hover:underline transition-colors"
          >
            {isSignUp ? "Already have an account? Sign In" : "Don't have a workspace account? Register"}
          </button>
        </div>
      </div>
    </div>
  );
}
