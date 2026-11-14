async function post(path, body) {
  const response = await fetch(`/api${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(270000),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail;

    const message = Array.isArray(detail)
      ? detail
          .map((item) => `${item.loc?.at(-1)}: ${item.msg}`)
          .join("; ")
      : typeof detail === "string"
        ? detail
        : `Request failed (${response.status}). Check that FastAPI is running.`;

    throw new Error(message);
  }

  if (!data) {
    throw new Error("The server returned an unreadable response.");
  }

  return data;
}

export function getProfile(inputs) {
  return post("/ai/profile", inputs);
}

export function getExplanation(inputs) {
  return post("/ai/profile/explain", inputs);
}

export function errorMessage(error) {
  if (["TimeoutError", "AbortError"].includes(error.name)) {
    return "The request timed out. Check the backend and Ollama, then retry.";
  }

  if (error instanceof TypeError) {
    return "Cannot reach the API. Check that FastAPI and the frontend are running.";
  }

  return error.message || "Something went wrong. Please retry.";
}