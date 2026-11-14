import { useState } from "react";
import { register } from "../services/auth";

export default function RegisterForm() {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function toggle() {
    setOpen((current) => !current);
    setPassword("");
    setConfirmation("");
    setError("");
    setSuccess("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (busy) return;

    setError("");
    setSuccess("");

    if (password !== confirmation) {
      setError("The passwords do not match.");
      return;
    }

    if (new TextEncoder().encode(password).length > 72) {
      setError("The password must not exceed 72 UTF-8 bytes.");
      return;
    }

    setBusy(true);

    try {
      await register(email.trim(), password);
      setPassword("");
      setConfirmation("");
      setOpen(false);
      setSuccess(
        "Account created. Sign in above using your email and password."
      );
    } catch (err) {
      if (["TimeoutError", "AbortError"].includes(err.name)) {
        setError(
          "The request timed out. Your account may have been created; " +
          "try signing in before registering again."
        );
      } else if (err instanceof TypeError) {
        setError("Cannot reach the server. Check that FastAPI is running.");
      } else {
        setError(err.message || "Registration failed.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mt-7 border-t border-rose-100 pt-5">
      <p className="text-sm text-slate-600">
        {open ? "Already have an account?" : "New to Luna Fit?"}{" "}
        <button
          type="button"
          onClick={toggle}
          disabled={busy}
          aria-expanded={open}
          aria-controls="registration-form"
          className="m-0 rounded-md bg-transparent px-1 py-1 font-semibold text-rose-600 underline underline-offset-4 hover:bg-rose-50"
        >
          {open ? "Back to sign in" : "Create an account"}
        </button>
      </p>

      {success && (
        <p
          role="status"
          className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800"
        >
          {success}
        </p>
      )}

      {open && (
        <form id="registration-form" onSubmit={handleSubmit}>
          <fieldset disabled={busy} className="m-0 space-y-4 p-0">
            <legend className="mb-3 text-lg font-semibold text-slate-800">
              Create your account
            </legend>

            <div>
              <label htmlFor="register-email">Email address</label>
              <input
                id="register-email"
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full max-w-none rounded-xl"
              />
            </div>

            <div>
              <label htmlFor="register-password">Password</label>
              <input
                id="register-password"
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                aria-describedby="register-password-hint"
                className="w-full max-w-none rounded-xl"
              />
              <p
                id="register-password-hint"
                className="text-xs text-slate-500"
              >
                Use at least 8 characters and a password you do not use elsewhere.
              </p>
            </div>

            <div>
              <label htmlFor="register-confirmation">
                Confirm password
              </label>
              <input
                id="register-confirmation"
                type="password"
                autoComplete="new-password"
                required
                value={confirmation}
                onChange={(event) => setConfirmation(event.target.value)}
                className="w-full max-w-none rounded-xl"
              />
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
              className="w-full rounded-xl bg-rose-500 text-white hover:bg-rose-600"
            >
              {busy ? "Creating account…" : "Create account"}
            </button>
          </fieldset>
        </form>
      )}
    </section>
  );
}