"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { User, signInWithPopup, signOut, onAuthStateChanged, signInWithEmailAndPassword, createUserWithEmailAndPassword } from "firebase/auth";
import { auth, googleProvider, hasFirebaseConfig } from "@/lib/firebase";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  loginWithGoogle: () => Promise<void>;
  loginWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isHistoryOpen: boolean;
  setHistoryOpen: (open: boolean) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  loginWithGoogle: async () => {},
  loginWithEmail: async () => {},
  signUpWithEmail: async () => {},
  logout: async () => {},
  isHistoryOpen: false,
  setHistoryOpen: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isHistoryOpen, setHistoryOpen] = useState(false);

  useEffect(() => {
    if (!hasFirebaseConfig) {
      const savedUser = localStorage.getItem("omnirag_mock_user");
      if (savedUser) {
        setUser(JSON.parse(savedUser));
      } else {
        setUser(null);
      }
      setLoading(false);
      return () => {};
    }

    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  const loginWithGoogle = async () => {
    if (!hasFirebaseConfig) {
      const mockUser = {
        uid: "google-guest-id",
        email: "google-guest@omnirag.local",
        displayName: "Google Guest",
        emailVerified: true,
      } as any;
      localStorage.setItem("omnirag_mock_user", JSON.stringify(mockUser));
      setUser(mockUser);
      return;
    }
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (error) {
      console.error("Google Sign-In failed:", error);
      throw error;
    }
  };

  const loginWithEmail = async (email: string, password: string) => {
    if (!hasFirebaseConfig) {
      const mockUser = {
        uid: "email-guest-id",
        email: email || "developer@omnirag.local",
        displayName: email ? email.split("@")[0] : "Local Developer",
        emailVerified: true,
      } as any;
      localStorage.setItem("omnirag_mock_user", JSON.stringify(mockUser));
      setUser(mockUser);
      return;
    }
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (error) {
      console.error("Email login failed:", error);
      throw error;
    }
  };

  const signUpWithEmail = async (email: string, password: string) => {
    if (!hasFirebaseConfig) {
      const mockUser = {
        uid: "email-guest-id",
        email: email,
        displayName: email.split("@")[0],
        emailVerified: true,
      } as any;
      localStorage.setItem("omnirag_mock_user", JSON.stringify(mockUser));
      setUser(mockUser);
      return;
    }
    try {
      await createUserWithEmailAndPassword(auth, email, password);
    } catch (error) {
      console.error("Email signup failed:", error);
      throw error;
    }
  };

  const logout = async () => {
    if (!hasFirebaseConfig) {
      localStorage.removeItem("omnirag_mock_user");
      setUser(null);
      return;
    }
    try {
      await signOut(auth);
    } catch (error) {
      console.error("Sign-out failed:", error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        loginWithGoogle,
        loginWithEmail,
        signUpWithEmail,
        logout,
        isHistoryOpen,
        setHistoryOpen,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

