import { descriptions } from "../config/profileConfig";

export default function ProfileResult({
  profile,
  busy,
  onExplain,
}) {
  if (!profile) {
    return (
      <section id="results">
        <h2>Your profile</h2>
        <p>Enter your habits or use the example, then explore your profile.</p>
      </section>
    );
  }

  const description = descriptions[profile.profile_id];

  return (
    <section id="results" aria-live="polite">
      <h2>
        {profile.profile_name || description?.name || "Your profile"}
      </h2>

      <p>{profile.description || description?.text}</p>

      <p>
        These descriptions summarize observed group patterns, not every
        member. Profiles are not ranked and do not define an ideal diet.
        Occupational activity is not included.
      </p>

      <button
        type="button"
        onClick={onExplain}
        disabled={Boolean(busy)}
      >
        {busy === "explanation"
          ? "Preparing your explanation…"
          : "Explain with Luna"}
      </button>
    </section>
  );
}