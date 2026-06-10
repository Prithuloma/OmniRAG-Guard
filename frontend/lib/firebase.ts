import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyCdTNnlAuUg246cwuYv-uzK_iQVkV0-Cb4",
  authDomain: "omnirag-1.firebaseapp.com",
  projectId: "omnirag-1",
  storageBucket: "omnirag-1.firebasestorage.app",
  messagingSenderId: "533356487987",
  appId: "1:533356487987:web:fa4db55cada72afde18a46",
  measurementId: "G-93091NVM5H"
};

// Initialize Firebase
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export { app, auth, googleProvider };
