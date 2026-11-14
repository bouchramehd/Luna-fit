export async function getCurrentUser(token) {
  const response = await fetch("/api/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal: AbortSignal.timeout(20000),
  });

  if (!response.ok) {
    throw new Error(
      response.status === 401
        ? "Your session has expired. Please sign in again."
        : "Could not load your account."
    );
  }

  return response.json();
}

export async function login(email, password) {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
    signal: AbortSignal.timeout(20000),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      response.status === 401
        ? "Email or password is incorrect."
        : response.status === 422
          ? "Please check your email and password."
          : "Sign-in is unavailable. Please try again."
    );
  }

  if (!data?.access_token) {
    throw new Error("The server returned an invalid login response.");
  }

  const user = await getCurrentUser(data.access_token);

  return {
    token: data.access_token,
    user,
  };
}

export async function register(email, password) {
  const response = await fetch("/api/users", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
    signal: AbortSignal.timeout(20000),
  });

  if (!response.ok) {
    if (response.status === 400) {
      throw new Error(
        "An account may already exist with this email. Try signing in."
      );
    }

    if (response.status === 422) {
      throw new Error("Please check your email and password.");
    }

    throw new Error("Registration is unavailable. Please try again.");
  }

  return response.json();
}