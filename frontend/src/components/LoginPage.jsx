import { useState } from "react";
import { login } from "../services/auth";
import RegisterForm from "./RegisterForm";

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (busy) return;

    setBusy(true);
    setError("");

    try {
      const session = await login(email.trim(), password);
      setPassword("");
      onLogin(session);
    } catch (err) {
      if (["TimeoutError", "AbortError"].includes(err.name)) {
        setError("Sign-in timed out. Please try again.");
      } else if (err instanceof TypeError) {
        setError("Cannot reach the server. Check that FastAPI is running.");
      } else {
        setError(err.message || "Sign-in failed. Please try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-rose-50 via-white to-purple-50 px-5 py-12">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-[2rem] border border-rose-100 bg-white shadow-xl shadow-rose-100/40 md:grid-cols-2">
        <aside className="relative hidden flex-col justify-between bg-gradient-to-br from-rose-100 to-purple-100 p-10 md:flex">
          <div className="text-xl font-bold tracking-widest text-rose-800">
            LUNA FIT
          </div>

          <div>
            <div
              aria-hidden="true"
              className="mb-8 flex h-28 w-28 items-center justify-center rounded-full border border-white/80 bg-white/50 text-6xl text-rose-400"
            >
              ◒
            </div>

            <h1 className="text-4xl leading-tight font-semibold tracking-tight text-slate-800">
              Your habits.
              <br />
              Your rhythm.
              <br />
              A little clarity.
            </h1>

            <p className="mt-5 max-w-sm text-sm leading-7 text-slate-600">
              Explore nutrition and activity patterns, understand your
              profile, and keep track of your cycle.
            </p>
          </div>

          <p className="text-xs text-slate-500">
            Thoughtful insights. Space for your own experience.
          </p>
        </aside>

        <main className="m-0 w-full max-w-none p-7 sm:p-12">
          <div className="mb-10 text-sm font-bold tracking-widest text-rose-600 md:hidden">
            LUNA FIT
          </div>

          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-500">
            WELCOME BACK
          </p>

          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-800">
            A moment for you
          </h2>

          <p className="mb-8 text-sm text-slate-500">
            Sign in to continue to your dashboard.
          </p>

          <form onSubmit={handleSubmit}>
            <fieldset disabled={busy} className="m-0 space-y-5 p-0">
              <legend className="sr-only">
                Sign in to Luna Fit
              </legend>

              <div>
                <label
                  htmlFor="login-email"
                  className="mb-2 mt-0 block text-sm font-medium text-slate-700"
                >
                  Email address
                </label>

                <input
                  id="login-email"
                  name="email"
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  className="w-full max-w-none rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-rose-400 focus:ring-2 focus:ring-rose-100"
                />
              </div>

              <div>
                <label
                  htmlFor="login-password"
                  className="mb-2 mt-0 block text-sm font-medium text-slate-700"
                >
                  Password
                </label>

                <div className="relative">
                  <input
                    id="login-password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="w-full max-w-none rounded-xl border border-slate-200 bg-slate-50 py-3 pl-4 pr-20 text-sm outline-none focus:border-rose-400 focus:ring-2 focus:ring-rose-100"
                  />

                  <button
                    type="button"
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                    aria-pressed={showPassword}
                    onClick={() => setShowPassword((current) => !current)}
                    className="absolute inset-y-0 right-0 m-0 rounded-r-xl rounded-l-none bg-transparent px-4 py-0 text-xs font-semibold text-rose-700 hover:bg-rose-50"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {error && (
                <p
                  role="alert"
                  className="rounded-xl bg-rose-50 p-3 text-sm text-rose-800"
                >
                  {error}
                </p>
              )}

              <button
                type="submit"
                className="m-0 w-full rounded-xl bg-rose-500 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-rose-600 disabled:cursor-wait disabled:opacity-60"
              >
                {busy ? "Signing in…" : "Sign in →"}
              </button>
            </fieldset>
          </form>

          <RegisterForm />

          <p className="mt-6 text-xs leading-6 text-slate-500">
            For this prototype, refreshing the page ends your session.
          </p>
        </main>
      </div>
    </div>
  );
}