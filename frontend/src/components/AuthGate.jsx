import { useEffect, useState } from "react";
import App from "../App";
import LoginPage from "./LoginPage";

export default function AuthGate() {
  const [session, setSession] = useState(null);
  const [notice, setNotice] = useState("");

  function handleLogin(result) {
    setNotice("");
    setSession({
      ...result,
      expiresAt: Date.now() + 55 * 60 * 1000,
    });
  }

  function logout() {
    setSession(null);
    setNotice("You have signed out.");
  }

  useEffect(() => {
    if (!session) return;

    const timer = window.setTimeout(() => {
      setSession(null);
      setNotice("Your session has ended. Please sign in again.");
    }, Math.max(0, session.expiresAt - Date.now()));

    return () => window.clearTimeout(timer);
  }, [session]);

  if (!session) {
    return (
      <>
        {notice && (
          <div
            role="status"
            className="bg-rose-50 px-5 py-3 text-center text-sm text-rose-800"
          >
            {notice}
          </div>
        )}
        <LoginPage onLogin={handleLogin} />
      </>
    );
  }

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-rose-100 bg-white px-6 py-3">
        <p className="m-0 text-sm text-slate-600">
          Signed in as{" "}
          <span className="font-semibold text-slate-800">
            {session.user.email}
          </span>
        </p>

        <button
          type="button"
          onClick={logout}
          className="m-0 rounded-full bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-100"
        >
          Sign out
        </button>
      </div>

      <App />
    </>
  );
}